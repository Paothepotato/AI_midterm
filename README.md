# Trò Chơi Sokoban Đơn và Đối Kháng (AI Project)

Dự án cài đặt các thuật toán tìm kiếm trí tuệ nhân tạo (UCS, A\*) cho bài toán Sokoban đơn người và mở rộng sang hệ thống mô phỏng thi đấu đối kháng giữa 2 Agent, phát triển bằng Python và Pygame.

## 📂 Cấu trúc dự án

```
├── core/
│   ├── board.py            # Mô hình biểu diễn bản đồ, tường, sàn, hộp và đích
│   ├── constants.py        # Các hướng di chuyển và hằng số chi phí
│   ├── coordinator.py      # Bộ điều phối xung đột va chạm và phá vỡ chu kỳ lặp
│   ├── deadlock.py         # Module nhận diện deadlock (góc chết, cạnh tường, khối 2x2)
│   ├── gui_theme.py        # Bảng màu chuẩn và hàm vẽ các thực thể trên Pygame
│   ├── heuristic.py        # Hàm Heuristic Hungarian gán cặp tối ưu trên lưới khoảng cách BFS
│   └── state.py            # Định nghĩa lớp trạng thái State và CompetitiveState
├── maps/                   # Tập các bản đồ thử nghiệm từ đơn giản đến phức tạp
├── task1/                  # Mô hình hóa không gian trạng thái Sokoban đơn người
├── task2/                  # Bộ giải tìm kiếm đồ thị với UCS và A*
├── task3/                  # Đo lường hiệu năng và xuất biểu đồ benchmark
├── task4/                  # Kiểm chứng tính Admissible và Consistent của Heuristic
├── task5/                  # Giao diện đồ họa Pygame cho chế độ một người chơi
├── task6/                  # Mô hình hóa bài toán đối kháng 2 Agent
├── task7/                  # Kịch bản mô phỏng đối kháng không qua GUI
└── task8/                  # Giao diện đồ họa Pygame đối kháng trực tiếp

```

## ⚙️ Hướng dẫn cài đặt

1. **Yêu cầu môi trường:** Python 3.8 trở lên.

2. **Cài đặt các thư viện phụ thuộc:**
   Mở terminal và chạy lệnh sau:

   ```
   pip install pygame numpy matplotlib scipy
   
   ```

## 🚀 Hướng dẫn chạy chương trình

Mở terminal tại thư mục gốc của dự án để thực thi các task cụ thể:

### 1. Chế độ đơn người (Tasks 1 - 5)

* **Chạy Task 1 (Kiểm chứng không gian trạng thái):**

  ```
  python task1/run_task1.py
  
  ```

* *Chạy Task 2 (Giải Sokoban bằng UCS và A):*\*

  ```
  python task2/run_task2.py
  
  ```

* **Chạy Task 3 (Thực nghiệm đo lường hiệu năng và xuất biểu đồ):**

  ```
  python task3/benchmark.py
  
  ```

* **Chạy Task 4 (Kiểm chứng Heuristic Admissible & Consistent):**

  ```
  python task4/verify_heuristic.py
  
  ```

* **Chạy Task 5 (Giao diện đồ họa đơn người):**

  ```
  python task5/gui_single.py maps/example_simple.txt astar
  # Hoặc sử dụng UCS:
  python task5/gui_single.py maps/example_simple.txt ucs
  
  ```

### 2. Chế độ đối kháng 2 Agent (Tasks 6 - 8)

* **Chạy Task 7 (Mô phỏng thi đấu 2 Agent qua dòng lệnh):**

  ```
  python task7/run_task7.py
  
  ```

* **Chạy Task 8 (Giao diện đồ họa thi đấu đối kháng trực tiếp):**

  ```
  python task8/gui_competitive.py maps/competitive_map.txt
  
  ```