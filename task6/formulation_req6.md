# BÁO CÁO MÔ HÌNH HÓA BÀI TOÁN SOKOBAN ĐỐI KHÁNG HAI AGENT
**Môn học:** Trí tuệ Nhân tạo (Introduction to Artificial Intelligence - 503043)  
**Phần thực hiện:** Báo cáo mô hình hóa đối kháng (Task 6)

---

### 1. Tổng quan bài toán (Problem Overview)
Bài toán mở rộng trò chơi đẩy hộp Sokoban kinh điển từ môi trường đơn agent (single-agent) thành trò chơi đối kháng giữa hai agent (two-player competitive game).
- **Mục tiêu:** Hai agent (Agent 0 và Agent 1) cùng thi đấu trên một bản đồ để đẩy các hộp vào các vị trí đích (designated positions/goals).
- **Quy tắc thời gian & bước đi:** Trận đấu diễn ra trong $n$ lượt đi đồng thời (với $n$ do người dùng nhập từ bàn phím). Ở mỗi lượt, cả hai agent phải đưa ra quyết định cùng một lúc.
- **Tính đối kháng:** Một agent được phép đẩy hộp mà đối thủ đã đưa vào đích ra khỏi đích đó để tước điểm của đối thủ và giành lại điểm cho mình.
- **Điều kiện thắng:** Sau đúng $n$ lượt, agent nào sở hữu nhiều hộp trên đích hơn sẽ giành chiến thắng.

---

### 2. Định nghĩa các thành phần hình thức (Formal Formulation)

#### 2.1. Tập người chơi (Players)
$$P = \{0, 1\}$$
- Player 0: Xuất phát tại vị trí ký hiệu `A`.
- Player 1: Xuất phát tại vị trí ký hiệu `Z`.

#### 2.2. Không gian trạng thái (State Space $S$)
Một trạng thái $s \in S$ được biểu diễn là một bộ dữ liệu bất biến:
$$s = (players, boxes, owners, turn)$$
Trong đó:
1. $players = (p_0, p_1)$: Cặp tọa độ ô lưới $(x, y)$ của Agent 0 và Agent 1 trên mặt sàn.
2. $boxes = (b_1, b_2, \dots, b_k)$: Bộ tuple tọa độ của $k$ hộp, luôn được chuẩn hóa sắp xếp tăng dần theo tọa độ $x$, sau đó đến $y$.
3. $owners = (o_1, o_2, \dots, o_k)$: Véc-tơ xác định chủ sở hữu tương ứng của từng hộp $b_j$:
   - $o_j = -1$: Hộp trung lập (chưa được agent nào đẩy vào đích, hoặc đang nằm ngoài đích).
   - $o_j = 0$: Hộp đang nằm trên đích và được ghi điểm bởi Agent 0.
   - $o_j = 1$: Hộp đang nằm trên đích và được ghi điểm bởi Agent 1.
4. $turn \in \{0, 1, \dots, n\}$: Số lượt đồng thời đã trôi qua.

#### 2.3. Trạng thái khởi tạo (Initial State $s_0$)
- $players = (pos(A), pos(Z))$.
- $boxes = boxes_{initial}$ (trích xuất từ map).
- $owners = (-1, -1, \dots, -1)$ (kể cả hộp đã nằm sẵn trên đích lúc đầu cũng chưa thuộc về ai).
- $turn = 0$.

#### 2.4. Không gian hành động (Action Space)
Mỗi agent $i \in \{0, 1\}$ có tập hành động rời rạc:
$$A_i = \{\text{North}, \text{East}, \text{West}, \text{South}, \text{Wait}\}$$
- Các hướng di chuyển tương ứng véc-tơ:
  - $\text{North} = (0, -1)$
  - $\text{East} = (1, 0)$
  - $\text{West} = (-1, 0)$
  - $\text{South} = (0, 1)$
  - $\text{Wait} = (0, 0)$
- Hành động kết hợp đồng thời tại mỗi lượt: $a = (a_0, a_1) \in A_0 \times A_1$.

#### 2.5. Mô hình chuyển trạng thái đồng thời (Transition Model $T(s, a) \rightarrow s'$)
Tại trạng thái $s$, với cặp hành động $a = (a_0, a_1)$:
1. **Xét ý định độc lập (Intentions):**
   - Với từng agent $i$, tính toán ô đích đến dự kiến $p'_i = p_i + dir(a_i)$.
   - Nếu $p'_i$ là ô sàn trống: hợp lệ (bước đi thường).
   - Nếu $p'_i$ có chứa hộp: kiểm tra ô tiếp theo sau hộp $p''_{box} = p'_i + dir(a_i)$. Nếu $p''_{box}$ là sàn trống (không có tường và không có hộp khác), ý định đẩy hộp hợp lệ.
   - Ngược lại: ý định không hợp lệ $\rightarrow$ agent đứng yên (`Wait`).

2. **Phân giải xung đột đồng thời (Conflict Resolution):**
   Cả hai agent cùng hành động tại một thời điểm. Xung đột được phân giải như sau:
   - **Xung đột cùng ô đến hoặc cùng đẩy một hộp (Quy tắc xác suất):**
     Nếu hai agent cùng cố gắng đi vào một vị trí ($p'_0 = p'_1$) hoặc cùng cố gắng đẩy chung một hộp tại vị trí $b_j$ ($b_{\text{from0}} = b_{\text{from1}}$), một biến ngẫu nhiên liên tục $p \sim \mathcal{U}(0, 1)$ được sinh ra:
     + Nếu $p < 0.5$: Agent 1 (Player 0) thực hiện hành động, Agent 2 (Player 1) đứng yên (mất lượt).
     + Nếu $p \ge 0.5$: Agent 2 (Player 1) thực hiện hành động, Agent 1 (Player 0) đứng yên (mất lượt).
   - **Các xung đột bất khả thi khác (Hủy cả hai hành động – đứng yên tại chỗ):**
     + **Xung đột đối đầu / đổi chỗ (Head-on swap):** $p'_0 = p_1 \land p'_1 = p_0$ (không được đi xuyên qua nhau).
     + **Xung đột vị trí tĩnh:** Agent $i$ không được bước vào hoặc đẩy hộp vào vị trí hiện tại của agent $1-i$.
     + **Xung đột hộp - người:** Ô đến của hộp bên này trùng ô đến của agent bên kia.
     + **Xung đột hộp - hộp:** Hai hộp được đẩy đến cùng một ô đích.

3. **Cập nhật quyền sở hữu (Ownership Dynamics):**
   - Nếu Agent $i$ đẩy thành công một hộp đến vị trí thuộc tập đích $G$: $owner = i$.
   - Nếu một hộp bị đẩy ra khỏi tập đích $G$: $owner = -1$ (chủ sở hữu cũ bị tước điểm).
   - Các hộp không bị tác động giữ nguyên trạng thái sở hữu.

4. **Tăng biến đếm:** $turn' = turn + 1$.

#### 2.6. Trạng thái kết thúc (Terminal Test)
Trận đấu kết thúc khi và chỉ khi:
$$\text{IsTerminal}(s) \iff s.turn \ge n$$
*(Lưu ý: Trận đấu không kết thúc sớm ngay cả khi tất cả các hộp đều đã nằm trên đích, nhằm tạo cơ hội cho các agent tranh cướp hộp cho đến lượt cuối cùng).*

#### 2.7. Hàm tiện ích & Điểm số (Utility / Payoff Function)
Điểm số của từng người chơi tại trạng thái $s$:
$$\text{Score}_0(s) = \sum_{j=1}^k \mathbb{I}(b_j \in G \land o_j = 0)$$
$$\text{Score}_1(s) = \sum_{j=1}^k \mathbb{I}(b_j \in G \land o_j = 1)$$
Hàm tiện ích (dưới góc nhìn đối kháng zero-sum):
$$U_0(s) = \text{Score}_0(s) - \text{Score}_1(s)$$
- $U_0(s) > 0$: Player 0 chiến thắng.
- $U_0(s) < 0$: Player 1 chiến thắng.
- $U_0(s) = 0$: Hòa cờ (Draw).

---

### 3. Thiết kế bản đồ thi đấu (`maps/competitive_map.txt`)
Để đảm bảo môi trường cạnh tranh công bằng và thú vị:
- **Kích thước rộng rãi ($15 \times 11$):** Đủ không gian để 2 agent điều hướng mà không bị kẹt ngay từ các bước đầu.
- **Tính đối xứng nghiêm ngặt (Strict Symmetry):** Vị trí xuất phát của $A$ và $Z$, cũng như các hộp và các đích được bố trí đối xứng hoàn hảo qua tâm bản đồ.
- **Khả năng cướp hộp (4-direction Accessibility):** Các ô đích $D$ được đặt tại các vị trí thoáng, có thể tiếp cận từ 4 hướng (tránh các góc chết/deadlock tường). Điều này cho phép một agent đẩy hộp vào đích từ một phía, và agent đối thủ hoàn toàn có thể tiếp cận từ phía đối diện để đẩy hộp ra khỏi đích, tạo nên tính cạnh tranh quyết liệt.
