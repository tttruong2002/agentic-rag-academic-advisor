# Evaluation

## Benchmark Dataset

- **150 câu hỏi** về quy chế đào tạo HCMUTE (`data/evaluation/150questions.txt` - đã bổ sung thêm 100 câu mới cho đợt nâng cấp lên Agentic RAG, Naive RAG cũ chỉ có 50 câu)
- Kiểm tra chất lượng: `root/Check_cauhoi_Huy.docx`

## Notebooks đánh giá

| Notebook | Mô tả | Model |
|---|---|---|
| `03_Evaluation_RAG.ipynb` (legacy) | Baseline RAG ban đầu | — |
| `04_Evaluation_Naive_RAG.ipynb` | Naive RAG, 150 câu | compound-mini |
| `05_Evaluation_Agentic_RAG.ipynb` | Agentic RAG so sánh | compound-mini + rewriter |

## Cơ chế đánh giá

### Judge LLM
- Dùng LLM chấm điểm câu trả lời (0-10) so với ground truth
- Regex Fallback: Khi Judge trả text thay vì JSON → regex bắt score
- Debug Logging: In chi tiết khi parse thất bại

### Robust Resume
- `score = 0` được coi là flag lỗi hệ thống (không phải điểm thật)
- Notebook tự động chạy tiếp (Resume) tại đúng câu lỗi thay vì từ đầu

### Flexible Re-generation
- Câu trả lời rỗng (empty answer) → tự động re-run

## Kết quả (Files)

| File | Nội dung |
|---|---|
| `evaluation_04_naive_rag.csv` | Kết quả 150 câu Naive RAG |
| `evaluation_05_agentic_rag_refined.csv` | Kết quả Agentic RAG |
| `evaluation_results_Alibaba.csv` | So sánh embedding Alibaba |
| `evaluation_results_MiniLM-L12-v2.csv` | So sánh embedding MiniLM |
| `evaluation_results_GroqCompoundMini.csv` | Kết quả GroqCompoundMini |
| `evaluation_summary.png` | Biểu đồ tổng hợp |
| `embedding_comparison.png` | So sánh embedding models |
| `score_vs_latency.png` | Biểu đồ điểm vs độ trễ |
