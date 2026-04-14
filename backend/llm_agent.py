# backend/llm_agent.py
import os
import re
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Kéo Retriever từ file vector_store.py mình vừa tạo sang đây
from backend.vector_store import get_retriever, format_context

# Biến Toàn cục chứa Model
llm_router = None
llm_generator = None
llm_rewriter = None

def init_agents():
    """ 
    Hàm này được gọi duy nhất 1 lần lúc bật server để kết nối với API Groq.
    Rút ruột toàn bộ mớ cấu hình rườm rà dưới main.py vứt lên cho sạch.
    """
    global llm_router, llm_generator, llm_rewriter

    print("⏳ [Agent] Đang kết nối mạng lưới đa Mô hình Groq...")
    try:
        llm_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
        llm_smart = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
        llm_gen = ChatGroq(model="groq/compound-mini", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

        # 1. Router Chain
        router_prompt = ChatPromptTemplate.from_template("""\
Bạn là hệ thống điều hướng câu hỏi cho sinh viên Trường ĐH Công Nghệ Kỹ Thuật TP.HCM (tên cũ là ĐH Sư phạm Kỹ thuật TP.HCM).
Dựa vào câu hỏi dưới đây, hãy xác định xem sinh viên đang:
1. Giao tiếp bình thường, chào hỏi, cảm ơn, hỏi thông tin về chính bản thân AI, hoặc gõ các ký tự vô nghĩa rác -> intent = "GREETING". (Nếu là ký tự vô nghĩa, hãy điền "Xin lỗi, tôi chưa hiểu ý bạn. Bạn có thể nói rõ hơn không?" vào "response")
2. Hỏi thông tin kiến thức về quy chế, chương trình học, điểm số, và các luật lệ ở trường -> intent = "RAG". ("response" để rỗng "")

Câu hỏi: {question}

YÊU CẦU NGHIÊM NGẶT: BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG 1 OBJECT JSON ĐƠN THUẦN. KHÔNG ĐƯỢC CHỨA BẤT KỲ VĂN BẢN TRÒ CHUYỆN NÀO KHÁC BÊN NGOÀI ĐOẠN JSON NÀY.
Cấu trúc JSON chuẩn:
{{"intent": "GREETING", "response": "Chào bạn..."}} hoặc {{"intent": "RAG", "response": ""}}"""
        )
        llm_router = router_prompt | llm_fast | JsonOutputParser()

        # 2. Generator Chain
        generator_prompt = ChatPromptTemplate.from_template("""\
Bạn là trợ lý AI hữu ích về quy chế học vụ ĐH Công Nghệ Kỹ Thuật TP.HCM (tên cũ là ĐH Sư phạm Kỹ thuật TP.HCM).
Nhiệm vụ: Đọc kỹ [Context] dưới đây để trả lời [Câu hỏi] và đánh giá xem context có đủ và đúng thông tin của người hỏi không.

[Context]
{context}

[Câu hỏi]
{question}

YÊU CẦU NGHIÊM NGẶT: BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG 1 OBJECT JSON ĐƠN THUẦN. KHÔNG ĐƯỢC CHỨA BẤT KỲ VĂN BẢN HAY DẤU MARKDOWN NÀO KHÁC QUANH JSON NÀY.
Cấu trúc JSON chuẩn:
{{"is_found": true hoặc false, "answer": "..."}}"""
        )
        llm_generator = generator_prompt | llm_gen | JsonOutputParser()

        # 3. Rewriter Chain
        rewriter_prompt = ChatPromptTemplate.from_template("""\
Bạn là một chuyên gia phân tích ngôn ngữ và học vụ của Trường ĐH Công Nghệ Kỹ Thuật TP.HCM (tên cũ là Sư phạm Kỹ thuật TP.HCM).
Câu hỏi gốc ban đầu của sinh viên: "{original_question}"
Câu truy vấn vừa được sử dụng để tìm kiếm nhưng thất bại: "{previous_query}"

Nhiệm vụ của bạn: Hãy phân tích ý định thực sự của sinh viên và tự suy luận ý nghĩa của các từ viết tắt, tiếng lóng, hoặc lỗi đánh máy dựa trên ngữ cảnh một trường Đại học Kỹ thuật (ví dụ: các ngành nghề như Robot và trí tuệ nhân tạo, Công nghệ thực phẩm, hoặc các nghiệp vụ như đăng ký môn học,...).
Sau đó, hãy viết lại thành MỘT CÂU TRUY VẤN MỚI tập trung vào các từ khóa chuẩn mực nhất để tìm kiếm ngữ nghĩa văn bản. Câu truy vấn mới phải rõ nghĩa và khác biệt so với câu đã thất bại.

YÊU CẦU TỐI THƯỢNG: BẠN CHỈ ĐƯỢC IN RA BLOCK MÃ JSON BÊN DƯỚI VÀ KHÔNG KÈM BẤT KỲ VĂN BẢN TRÒ CHUYỆN NÀO:
```json
{{"rewritten_query": "câu truy vấn mới ở đây"}}
```"""
        )
        llm_rewriter = rewriter_prompt | llm_smart | JsonOutputParser()

        print("✅ [Agent] Hệ thống Multi Agent đã sẵn sàng!")
    except Exception as e:
        print(f"❌ [Agent] Lỗi Khởi tạo Agent: {e}")

# ==============================================================================
# QUAN TRỌNG: Đây là hàm lõi để Tái Sử Dụng ở cả API lẫn file Jupyter Notebook 03!
# Thay vì nằm cứng ở @app.post, giờ ta kéo logic Vòng Lặp thành Hàm Python riêng.
# ==============================================================================
def run_agentic_rag(question: str, max_retries: int = 1):
    """
    Thực thi 1 câu hỏi từ đầu đến cuối xuyên qua lưới Agentic RAG.
    Trả về bộ Tuple: (final_answer, accumulated_context, intent, retries)
    """
    if not llm_generator or not llm_router:
        return ("Hệ thống chưa load xong Model.", "", "ERROR", 0)

    # Bước 1: Routing (Kiểm định)
    try:
        router_res = llm_router.invoke({"question": question})
        if str(router_res.get("intent", "")).strip().upper() == "GREETING":
            return (
                str(router_res.get("response", "Xin chào! Tôi có thể giúp gì cho bạn?")), 
                "", 
                "GREETING", 
                0
            )
    except Exception as e:
        print(f"[Router Fallback] Lỗi Router, chuyển thẳng vô RAG: {e}")

    # Bước 2: Vòng lặp RAG & Self-Correction
    retriever = get_retriever() # Gọi hàm từ vector_store.py
    current_query = question
    retries = 0
    final_answer = ""
    accumulated_context = ""

    while retries <= max_retries:
        print(f"🔄 [Rewriter Loop {retries}/{max_retries}] Đang quét với Query: {current_query}")
        
        try:
            # Truy xuất tài liệu
            docs = retriever.invoke(current_query)
            context = format_context(docs)
            accumulated_context = context # Ghi nhớ context để trả ra
            
            # Sinh câu trả lời & Đánh giá (Generate & Evaluate)
            gen_res = llm_generator.invoke({"context": context, "question": current_query})
            final_answer = str(gen_res.get("answer", ""))
            is_found = bool(gen_res.get("is_found", False))
            
            if is_found:
                print("✅ Tìm thấy thông tin, trả về kết quả.")
                break # Kết thúc sớm
                
            else:
                if retries < max_retries:
                    print("⚠️ Context không đủ dữ kiện, Model đang lên kết hoạch viết lại từ khóa search...")
                    try:
                        rewrite_res = llm_rewriter.invoke({
                            "original_question": question,
                            "previous_query": current_query
                        })
                        new_query = str(rewrite_res.get("rewritten_query", current_query))
                    except Exception as parse_err:
                        err_str = str(parse_err)
                        print(f"❌ Lỗi Parser Rewriter (LLM sinh text thừa): {err_str}")
                        # Dùng Regex Cứu Viện
                        match = re.search(r'\{.*"rewritten_query"\s*:\s*"[^"]+".*?\}', err_str, re.DOTALL)
                        if match:
                            try:
                                fallback_json = json.loads(match.group(0))
                                new_query = str(fallback_json.get("rewritten_query", current_query))
                                print(f"✅ Đã cứu dữ liệu thành công bằng Regex!")
                            except:
                                new_query = current_query + f" (thử tiếp từ khoá khác {retries})"
                        else:
                            new_query = current_query + f" (thử tiếp từ khoá khác {retries})"
                        
                    print(f"✨ Rewritten Query đổi thành: '{new_query}'")
                    current_query = new_query
                else:
                    print("⛔ Đã hết lượt thử nghiệm.")

        except Exception as e:
            final_answer = f"Xin lỗi, hệ thống gặp lỗi nội suy vòng lặp. Cụ thể: {str(e)}"
            print(f"Error Gen: {e}")
            break
            
        retries += 1

    intent_val = "RAG"
    final_retry_count = retries if retries <= max_retries else max_retries
    return (final_answer, accumulated_context, intent_val, final_retry_count)
