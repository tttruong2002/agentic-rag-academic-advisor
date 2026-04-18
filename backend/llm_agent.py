# backend/llm_agent.py
import os
import re
import json
import random
from groq import RateLimitError, BadRequestError
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Kéo Retriever từ file vector_store.py mình vừa tạo sang đây
from backend.vector_store import get_retriever, format_context

# ==============================================================================
# HỆ THỐNG KEY ROTATION — Đọc tất cả key từ .env, an toàn không lộ ra code.
# GROQ_API_KEY   = key mặc định (index 0)
# GROQ_API_KEY_1 = key dự phòng thứ 1 (index 1)  ... và cứ thế tiếp
#
# ⚠️  LỖI THIẾT KẾ ĐÃ SỬA (14/04/2026):
#     LangChain ChatGroq bind cứng api_key tại thời điểm khởi tạo.
#     Sau khi xoay key (_rotate_key), phải rebuild lại tất cả chain với key mới,
#     nếu không vẫn dùng key cũ → tất cả 9 lần xoay đều thất bại như nhau.
#     Giải pháp: lưu prompt templates làm global, gọi _rebuild_all_chains() trong _rotate_key().
# ==============================================================================
_groq_keys: list[str] = []
_current_key_idx: int = 0

# Tên model — đặt hằng số để dễ chỉnh sửa ở 1 chỗ
_MODEL_ROUTER  = "llama-3.1-8b-instant"
_MODEL_GEN     = "groq/compound-mini"     # Generator chính
_MODEL_GEN2    = "llama-3.3-70b-versatile" # Tầng dự phòng: Model xịn thứ 2 với context rộng
_MODEL_REWRITE = "groq/compound"          # Phù hợp với việc suy luận và tìm kiếm từ khóa phù hợp hơn

# Prompt templates — lưu global để _rebuild_all_chains() có thể dùng lại
_router_prompt_tmpl    = None
_generator_prompt_tmpl = None
_rewriter_prompt_tmpl  = None


def _load_groq_keys() -> list[str]:
    """
    Quét .env thu thập toàn bộ key GROQ.
    Thực hiện ngẫu nhiên hóa (shuffle) danh sách để cân bằng tải giữa các key,
    tránh việc lúc nào cũng dùng key đầu tiên dẫn đến chạm Rate Limit liên tục.
    """
    keys = []
    default = os.getenv("GROQ_API_KEY")
    if default:
        keys.append(default)
    i = 1
    while True:
        k = os.getenv(f"GROQ_API_KEY_{i}")
        if k is None:
            break
        if k not in keys:
            keys.append(k)
        i += 1
    
    # Ngẫu nhiên hóa thứ tự key
    random.shuffle(keys)
    return keys


def _get_current_key() -> str:
    return _groq_keys[_current_key_idx] if _groq_keys else os.getenv("GROQ_API_KEY", "")


def _rebuild_all_chains(key: str):
    """
    Khởi tạo lại TẤT CẢ LangChain chains với API key mới.
    Phải gọi hàm này SAU MỖI LẦN xoay key để tránh dùng key cũ.
    """
    global llm_router, llm_generator, llm_generator2, llm_rewriter
    llm_router     = _router_prompt_tmpl    | ChatGroq(model=_MODEL_ROUTER,  temperature=0,   api_key=key) | JsonOutputParser()
    llm_generator  = _generator_prompt_tmpl | ChatGroq(model=_MODEL_GEN,     temperature=0,   api_key=key) | JsonOutputParser()
    llm_generator2 = _generator_prompt_tmpl | ChatGroq(model=_MODEL_GEN2,    temperature=0,   api_key=key) | JsonOutputParser()
    llm_rewriter   = _rewriter_prompt_tmpl  | ChatGroq(model=_MODEL_REWRITE, temperature=0.3, api_key=key) | JsonOutputParser()
    print(f"   🔧 [Rebuild] Tất cả chain đã được tạo lại với Key #{_current_key_idx + 1}: ...{key[-6:]}")


def _rotate_key(reason: str = "Rate Limit") -> str:
    """
    Đổi sang key tiếp theo NGAY LẬP TỨC và rebuild tất cả chain.
    Không rebuild → chain vẫn dùng key cũ → xoay key vô nghĩa!
    """
    global _current_key_idx
    _current_key_idx = (_current_key_idx + 1) % len(_groq_keys)
    new_key = _groq_keys[_current_key_idx]
    print(f"   🔄 [Key Rotation / {reason}] Đổi sang Key #{_current_key_idx + 1}/{len(_groq_keys)}: ...{new_key[-6:]}")
    # ❗ Quan trọng: rebuild chain với key mới ngay lập tức
    _rebuild_all_chains(new_key)
    return new_key


# Biến Toàn cục chứa Model
llm_router     = None
llm_generator  = None   # compound (mạnh hơn, ưu tiên trước)
llm_generator2 = None   # compound-mini (fallback nếu compound bị Limit)
llm_rewriter   = None


def init_agents():
    """
    Hàm này được gọi duy nhất 1 lần lúc bật server để kết nối với API Groq.
    Rút ruột toàn bộ mớ cấu hình rườm rà dưới main.py vứt lên cho sạch.
    """
    global _groq_keys, _router_prompt_tmpl, _generator_prompt_tmpl, _rewriter_prompt_tmpl

    # Load toàn bộ key từ .env
    _groq_keys = _load_groq_keys()
    print(f"🔑 [Agent] Tìm thấy {len(_groq_keys)} Groq API Key để xoay vòng.")

    print("⏳ [Agent] Đang kết nối mạng lưới đa Mô hình Groq...")
    try:
        # 1. Router Prompt (Tối ưu Caching)
        _router_prompt_tmpl = ChatPromptTemplate.from_template("""\
VAI TRÒ: Bạn là chuyên gia điều hướng (Router) cho hệ thống học vụ ĐH Công Nghệ Kỹ Thuật TP.HCM.
NHIỆM VỤ: Phân loại ý định của [Câu hỏi] để quyết định luồng xử lý.

ĐỊNH DẠNG TRẢ VỀ (JSON ONLY):
{{"intent": "GREETING", "response": "Nếu là chào hỏi/xã giao, hãy trả lời tại đây"}} 
{{"intent": "RAG", "response": ""}} (Nếu hỏi về kiến thức/quy chế học vụ)

==================================================
[Câu hỏi]: {question}""")

        # 2. Generator Prompt (Tối ưu Caching - Trích xuất chi tiết)
        # LƯU Ý CHO AI SAU: Tuyệt đối giữ VAI TRÒ và NGUYÊN TẮC ở ĐẦU template này.
        # Groq sử dụng Prefix Matching để Cache. Nếu để {context} lên đầu, Cache sẽ vô dụng.
        _generator_prompt_tmpl = ChatPromptTemplate.from_template("""\
VAI TRÒ: Bạn là chuyên gia về quy chế đào tạo và công tác sinh viên của ĐH Công Nghệ Kỹ Thuật TP.HCM.
NHIỆM VỤ: Trả lời [Câu hỏi] bằng cách trích xuất dữ liệu từ [Context].

NGUYÊN TẮC TRẢ LỜI:
1. GROUNDING CHI TIẾT: Phải nêu rõ nội dung có trong văn bản cung cấp. CẤM trả lời chung chung 'thông tin nằm trong tài liệu X'.
2. TRUNG THỰC: Chỉ dùng thông tin trong context. Nếu không thấy thông tin chính xác, đặt "is_found": false.
3. NGẮN GỌN & ĐỦ Ý: Trả về câu trả lời súc tích.

ĐỊNH DẠNG TRẢ VỀ (JSON ONLY):
{{
  "is_found": true/false,
  "answer": "Nội dung trả lời chi tiết chiết xuất từ context. Nếu không thấy thông tin trong context thì trả về 'Không tìm thấy thông tin trong tài liệu'"
}}

==================================================
[Context]:
{context}

[Câu hỏi]: {question}""")

        # 3. Rewriter Prompt (Tối ưu Caching)
        _rewriter_prompt_tmpl = ChatPromptTemplate.from_template("""\
VAI TRÒ: Chuyên gia tối ưu truy vấn học thuật.
NHIỆM VỤ: Viết lại [Câu gốc] thành 1 câu truy vấn mới súc tích, mang tính gợi mở để tìm kiếm hiệu quả hơn.
NGUYÊN TẮC:
1. KHÔNG lặp lại các câu đã thử thất bại (nếu danh sách này có dữ liệu).
2. Tập trung vào các từ khóa then chốt của quy chế đại học.
3. LUÔN LUÔN viết truy vấn mới bằng tiếng Việt.

ĐỊNH DẠNG TRẢ VỀ (JSON ONLY):
{{"rewritten_query": "Nội dung câu truy vấn mới BẰNG tiếng Việt"}}

==================================================
[Câu gốc]: "{original_question}"
[Đã thử thất bại]:
{failed_queries_str}

[Query mới]:""")

        # Khởi tạo tất cả chain với key đầu tiên
        _rebuild_all_chains(_get_current_key())

        print("✅ [Agent] Hệ thống Multi Agent đã sẵn sàng!")
    except Exception as e:
        print(f"❌ [Agent] Lỗi Khởi tạo Agent: {e}")


# ==============================================================================
# QUAN TRỌNG: Đây là hàm lõi để Tái Sử Dụng ở cả API lẫn file Jupyter Notebook 03!
# Thay vì nằm cứng ở @app.post, giờ ta kéo logic Vòng Lặp thành Hàm Python riêng.
# ==============================================================================
def _invoke_with_key_rotation(chain_fn, inputs: dict, chain_name: str = ""):
    """
    Gọi bất kỳ LangChain chain nào với cơ chế xoay Key khi gặp RateLimitError.
    Sau mỗi lần xoay, _rotate_key() sẽ tự động rebuild chain → dùng đúng key mới.
    chain_fn: lambda nhận inputs và gọi chain (ví dụ: lambda inp: llm_router.invoke(inp))
    """
    keys_tried = 0
    while keys_tried < max(len(_groq_keys), 1):
        try:
            return chain_fn(inputs)
        except RateLimitError:
            print(f"   ⚠️ [{chain_name}] Rate Limit!")
            _rotate_key(f"Rate Limit [{chain_name}]")
            keys_tried += 1
        except Exception as e:
            raise e
    raise Exception(f"[{chain_name}] Tất cả {len(_groq_keys)} key đều bị Rate Limit.")


def _debug_413(inputs: dict, label: str = ""):
    """
    Debug helper: in ra kích thước các field trong inputs khi gặp lỗi 413.
    Giúp xác định field nào đang quá lớn gây Request Entity Too Large.
    """
    print(f"\n{'='*60}")
    print(f"\u274c [DEBUG 413 / {label}] Request Entity Too Large! Xác định field quá lớn:")
    
    # Khởi tạo một Model giả lập độc lập chỉ để gọi hàm get_num_tokens một cách chính xác
    # (Tránh gọi trực tiếp trên RunnableSequence llm_generator gây lỗi)
    dummy_tokenizer = ChatGroq(api_key=_get_current_key(), model=_MODEL_GEN)
    
    total = 0
    total_tokens = 0
    for k, v in inputs.items():
        size = len(str(v))
        total += size
        try:
            # Lấy token tính MỘT CÁCH CHÍNH XÁC
            exact_tokens = dummy_tokenizer.get_num_tokens(str(v))
            total_tokens += exact_tokens
            token_str = f"{exact_tokens:,} token (Chính xác)"
        except Exception:
            exact_tokens = size // 3
            total_tokens += exact_tokens
            token_str = f"~{exact_tokens:,} token (Ước tính)"
        
        status = "💡"
        print(f"   Field '{k}': {size:,} ký tự | {token_str} | {status}")
        if size > 500:
            # In 200 ký tự đầu để xem nội dung
            print(f"   Preview: {str(v)[:200].replace(chr(10), ' ')}...")
    print(f"   Tổng: {total:,} ký tự (Cỡ {total_tokens:,} token)")
    print(f"{'='*60}\n")


def _invoke_generator(inputs: dict):
    """
    Gọi Generator với chiến lược fallback 2 tầng:
    1️⃣  compound (mạnh) bị Rate Limit
    2️⃣  → thử compound-mini CÙNG KEY trước (tiết kiệm key)
    3️⃣  cả 2 đều bị Limit → xoay qua Key mới + rebuild chain → lặp lại từ đầu

    ⚠️  Lỗi 413 (Request Too Large) KHÔNG nên xoay key — xoay cũng không giúp được.
         413 xảy ra khi context quá lớn. Debug: dùng _debug_413() để xem field nào phình.
    Sau khi xoay key, _rotate_key() tự rebuild llm_generator & llm_generator2
    với key mới nên vòng lặp tiếp theo sẽ dùng đúng key mới.
    """
    keys_tried = 0
    while keys_tried < max(len(_groq_keys), 1):
        # Tầng 1: Model chính (thường là compound-mini)
        try:
            return llm_generator.invoke(inputs)
        except RateLimitError:
            print(f"   ⚠️ [Generator/{_MODEL_GEN}] Rate Limit! → Fallback sang {_MODEL_GEN2}...")
        except Exception as e:
            # 413: Request quá lớn — in debug thông số và prompt đầy đủ
            if "413" in str(e) or "request_too_large" in str(e).lower():
                _debug_413(inputs, f"Generator/{_MODEL_GEN}")
                
                # Lưu toàn bộ chuỗi gửi cho LLM ra file text (tránh bị terminal render thêm chữ)
                try:
                    # Truy cập vào mảng các message và lấy content thực sự của HumanMessage
                    raw_prompt_text = _generator_prompt_tmpl.invoke(inputs).messages[0].content
                    with open("debug_prompt_payload.txt", "w", encoding="utf-8") as f:
                        f.write(raw_prompt_text)
                    print("   📁 Đã xuất toàn bộ Prompt thô ra file 'debug_prompt_payload.txt' để bạn dễ nhìn.")
                except Exception as ex:
                    print(f"   ⚠️ Lỗi xuất prompt ra file: {ex}")
                    
            raise e

        # Tầng 2: Model dự phòng (thường là llama 70bm cùng key, tiết kiệm)
        try:
            return llm_generator2.invoke(inputs)
        except RateLimitError:
            print(f"   ⚠️ [Generator/{_MODEL_GEN2}] Rate Limit! → Xoay qua Key mới + rebuild chain...")
            # _rotate_key tự rebuild ALL chains với key mới
            _rotate_key(f"Generator {_MODEL_GEN} & {_MODEL_GEN2} đều Limit")
            keys_tried += 1
        except Exception as e:
            if "413" in str(e) or "request_too_large" in str(e).lower():
                _debug_413(inputs, f"Generator/{_MODEL_GEN2}")
                try:
                    raw_prompt_text = _generator_prompt_tmpl.invoke(inputs).messages[0].content
                    with open("debug_prompt_payload.txt", "w", encoding="utf-8") as f:
                        f.write(raw_prompt_text)
                except:
                    pass
            raise e

    raise Exception(f"[Generator] Tất cả {len(_groq_keys)} key và cả 2 model đều bị Rate Limit.")


def run_agentic_rag(question: str, max_retries: int = 1, prev_failed: list[str] = None, skip_router: bool = False):
    """
    Thực thi 1 câu hỏi từ đầu đến cuối xuyên qua lưới Agentic RAG.
    Trả về bộ Tuple: (final_answer, accumulated_context, intent, retries, is_found, failed_queries)
    """
    if not llm_generator or not llm_router:
        return ("Hệ thống chưa load xong Model.", "", "ERROR", 0, False, [])

    # Bước 1: Routing (Kiểm định) — có Key Rotation
    if not skip_router:
        try:
            router_res = _invoke_with_key_rotation(
                lambda inp: llm_router.invoke(inp), {"question": question}, "Router"
            )
            if str(router_res.get("intent", "")).strip().upper() == "GREETING":
                return (
                    str(router_res.get("response", "Xin chào! Tôi có thể giúp gì cho bạn?")),
                    "",
                    "GREETING",
                    0,
                    True,
                    []
                )
        except Exception as e:
            # Log chi tiết nếu có response từ Groq
            detailed_msg = getattr(e, "response", None)
            if detailed_msg:
                print(f"[Router Fallback] Lỗi Router, payload: {detailed_msg}")
            else:
                print(f"[Router Fallback] Lỗi Router, chuyển thẳng vô RAG: {e}")

    # Bước 2: Vòng lặp RAG & Self-Correction
    retriever = get_retriever() # Gọi hàm từ vector_store.py
    current_query = question
    failed_queries: list[str] = prev_failed.copy() if prev_failed else []  # Kế thừa lịch sử nếu có
    retries = 0
    final_answer = ""
    accumulated_context = ""

    while retries <= max_retries:
        print(f"🔄 [Rewriter Loop {retries}/{max_retries}] Đang quét với Query: {current_query}")

        try:
            # Truy xuất tài liệu
            docs = retriever.invoke(current_query)
            context = format_context(docs)
            accumulated_context = context

            # Sinh câu trả lời & Đánh giá — fallback 2 tầng (compound → compound-mini → key mới)
            gen_res = _invoke_generator(
                {"context": context, "question": current_query}
            )
            final_answer = str(gen_res.get("answer", ""))
            is_found = bool(gen_res.get("is_found", False))

            if is_found:
                print("✅ Tìm thấy thông tin, trả về kết quả.")
                break # Kết thúc sớm

            else:
                # Ghi nhận query này vào lịch sử thất bại
                failed_queries.append(current_query)  # LLM cần biết tất cả attempt trước để không lặp lại

                if retries < max_retries:
                    print("⚠️ Context không đủ dữ kiện, Model đang lên kế hoạch viết lại từ khóa search...")
                    # Format danh sách query đã thất bại thành chuỗi cho Prompt
                    failed_str = "\n".join(f"- {q}" for q in failed_queries) # Prompt nhận: "Các câu đã thử nhưng THẤT BẠI (KHÔNG được lặp lại)"
                    
                    try:
                        rewrite_res = _invoke_with_key_rotation(
                            lambda inp: llm_rewriter.invoke(inp),
                            {
                                "original_question": question,
                                "failed_queries_str": failed_str
                            },
                            "Rewriter"
                        )
                        new_query = str(rewrite_res.get("rewritten_query", current_query))
                    except json.JSONDecodeError as json_err:
                        print(f"❌ Lỗi Parser JSON Rewriter: {json_err}. Thử dùng Regex cứu dữ liệu...")
                        # Regex Fallback khi LLM trả về text thay vì JSON thuần
                        match = re.search(r'\{.*"rewritten_query"\s*:\s*"[^"]+".*?\}', str(json_err.doc if hasattr(json_err, 'doc') else json_err), re.DOTALL)
                        if match:
                            try:
                                new_query = str(json.loads(match.group(0)).get("rewritten_query", current_query))
                                print("✅ Đã cứu câu query từ JSON lỗi thành công!")
                            except:
                                new_query = current_query # Không dùng (retry x) vô nghĩa
                        else:
                            new_query = current_query
                    except Exception as api_err:
                        # Lỗi API thực sự (như 413, Rate Limit hết key...)
                        print(f"❌ Lỗi API Rewriter: {api_err}")
                        new_query = current_query # Giữ nguyên để loop tiếp hoặc thoát

                    print(f"✨ Rewritten Query đổi thành: '{new_query}'")
                    current_query = new_query
                else:
                    print("⛔ Đã hết số lần thử tìm kiếm lại (max_retries) nhưng vẫn không tìm thấy kết quả.")

        except Exception as e:
            final_answer = f"Xin lỗi, hệ thống gặp lỗi nội suy vòng lặp. Cụ thể: {str(e)}"
            print(f"Error Gen: {e}")
            is_found = False
            break

        retries += 1

    intent_val = "RAG"
    final_retry_count = retries if retries <= max_retries else max_retries
    # Đảm bảo is_found luôn được xác định (mặc định False nếu thoát vòng lặp mà chưa kịp gán)
    try:
        if 'is_found' not in locals(): is_found = False
    except:
        is_found = False
        
    return (final_answer, accumulated_context, intent_val, final_retry_count, is_found, failed_queries)
