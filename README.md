# Sokoban AI Project (Midterm)

Dự án bài tập lớn môn Nhập môn Trí tuệ Nhân tạo - Game Sokoban.

## Cấu trúc thư mục

- `core/`: Các module lõi mô hình hóa bàn cờ, trạng thái, hàm heuristic và môi trường đối kháng.
  - `board.py`: Đọc bản đồ, kiểm tra tính hợp lệ, luật di chuyển và sinh trạng thái kế tiếp.
  - `state.py`: Biểu diễn trạng thái đơn người (`State`) và đối kháng hai người (`CompetitiveState`).
  - `constants.py`: Các hằng số, hành động (North, South, East, West, Wait) và ký hiệu bản đồ.
  - `heuristic.py`: Hàm Heuristic Hungarian BFS và thuật toán cắt tỉa deadlock tĩnh.
  - `competition.py`: Quản lý lượt đấu, giải quyết xung đột đồng thời trong chế độ đối kháng.
- `maps/`: Tập hợp các bản đồ thử nghiệm từ đơn giản đến phức tạp.
- `task1/`: Mô hình hóa không gian trạng thái Sokoban (`run_task1.py`).
- `task2/`: Thuật toán tìm kiếm UCS và A* (`solver.py`, `run_task2.py`).
- `task3/`: Đo lường thực nghiệm và so sánh độ phức tạp không gian / thời gian giữa UCS và A* (`benchmark.py`).
- `task4/`: Chứng minh và kiểm chứng thực nghiệm tính chất Admissible & Consistent của hàm Heuristic (`verify_heuristic.py`).
- `task7/`: Mô phỏng trận đấu đối kháng Sokoban 2 Agent (`runner.py`, `agent_astar.py`, `agent_bfs.py`, `run_task7.py`).

## Hướng dẫn chạy thử nghiệm

Yêu cầu môi trường: Python 3.10+ (cần thư viện `scipy`, `matplotlib`, `numpy`).

```bash
# Cài đặt thư viện phụ thuộc (nếu chưa có)
pip install scipy matplotlib numpy

# Chạy thử nghiệm Task 1
python task1/run_task1.py

# Chạy thử nghiệm Task 2 (UCS vs A*)
python task2/run_task2.py

# Chạy thực nghiệm Task 3 (Benchmark toàn diện)
python task3/benchmark.py

# Kiểm chứng tính chất Heuristic Task 4
python task4/verify_heuristic.py

# Mô phỏng trận đối kháng Task 7
python task7/run_task7.py
```