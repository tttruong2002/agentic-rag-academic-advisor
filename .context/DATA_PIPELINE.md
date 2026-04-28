# Data Pipeline

## Nguồn dữ liệu

**44 file PDF** từ HCMUTE (thư mục `data/raw/`), bao gồm:
- Quy chế đào tạo trình độ đại học (QĐ 3116)
- Sổ tay sinh viên 2025
- Quy định đánh giá điểm rèn luyện
- Chương trình đào tạo các ngành (CNTT, KTDL, ATTT, ...)
- Quy định ngoại ngữ, chuyển điểm
- Thông báo đăng ký học phần, xét tốt nghiệp
- Biểu đồ kế hoạch giảng dạy
- Quy tắc văn hóa ứng xử

**Tổng dung lượng**: ~100MB PDF  
**Lưu ý**: `data/raw/` nằm trong `.gitignore` (đỡ nặng Github vì khi deploy thì cái này không cần thiết)

## Pipeline hiện tại (Legacy)

```
PDF files
  ↓
[01_Raw_Extraction.ipynb]
  ├── Docling → raw text (giữ cấu trúc Markdown)
  └── UnstructuredPDFLoader → raw text (flat text)
  ↓
[02_Refinement_Merge.ipynb]
  ├── Gộp 2 kết quả raw
  ├── Gemini Flash API → clean Vietnamese text
  └── Output: data/processed/merged_documents.txt (1.7MB)
  ↓
[Chunking + Embedding]
  ├── Token-based chunking (hiện tại)
  ├── Alibaba-NLP/gte-multilingual-base (CPU)
  └── ChromaDB: 6,655 vectors, 6 collections
```

## Vấn đề đã biết

1. **Context bị đứt gãy**: Chunk chỉ chứa nội dung, thiếu tiêu đề phân mảnh ở chunk trước
2. **Ký tự rác**: Header/footer/số trang PDF trộn vào text
3. **Bảng biểu vỡ**: PDF scan + bảng phức tạp → text trùng lặp khi parse (xem `docs/groq_api_issues_log.md` mục 2)

## Pipeline mới (Định hướng)

```
PDF files
  ↓
[00_Gemini_PDF_Parser.ipynb] (CHƯA VIẾT)
  ├── Upload PDF trực tiếp lên Gemini Files API
  ├── Gemini 2.5 Flash, Gemini 3 Flash (1M token context, Vision)
  ├── Context Caching: Lưu tạm (cache) file PDF đã tải lên để tiết kiệm token/chi phí khi truy vấn lại nhiều lần
  ├── Batch: ~10-20 trang/lần (tránh 65K output limit)
  ├── Bảng biểu → JSON Minified
  └── Output: clean Markdown Vietnamese text
  ↓
[Semantic Chunking]
  ├── MarkdownHeaderTextSplitter (thay vì token-based)
  ├── Mỗi chunk gắn metadata tiêu đề nguồn gốc
  └── Giải quyết vấn đề context đứt gãy
  ↓
[Embedding + ChromaDB]
  ├── Alibaba-NLP/gte-multilingual-base (giữ nguyên)
  └── Nạp lại toàn bộ data
```

## ChromaDB Collections hiện có

| Collection | Mô tả |
|---|---|
| `academic_regulations` | **Collection chính** đang dùng |
| `academic_regulations_MiniLM-L12-v2` | Thử nghiệm embedding model khác |
| `academic_regulations_test` | Test collection |
| `raw_docling_collection` | Raw output từ Docling |
| `raw_unstructured_collection` | Raw output từ Unstructured |
| `refined_pages_collection` | Sau bước refine |
