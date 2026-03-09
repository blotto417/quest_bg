# ⚔️ Quest: Avalon — Discord Bot

Bot Discord để chơi **Quest: Avalon** cho 2–10 người (4–10 người theo luật chuẩn, 2–3 người cho chế độ test).

---

## Cài Đặt

```bash
pip install -r requirements.txt
cp .env.example .env
# Dán token bot vào file .env
python3 bot.py
```

Cần bật **Server Members Intent** trong [Discord Developer Portal](https://discord.com/developers/applications).

---

## Luật Chơi

### Mục Tiêu

| Phe | Thắng khi |
|-----|-----------|
| ⚔️ **Thiện** | Hoàn thành 3 Nhiệm Vụ thành công, HOẶC đúng hết kẻ Ác trong Cơ Hội Cuối Cùng |
| 💀 **Ác** | Làm thất bại 3 Nhiệm Vụ, HOẶC Thợ Săn Mù đoán đúng 2 người Thiện theo vai trò |

---

### Lễ Đêm (Night Phase)

Khi game bắt đầu, mỗi người chơi nhận **DM** chứa:

- Thẻ vai trò của họ
- Thông tin ban đêm (ai thuộc phe nào, theo từng vai trò)

**Thông tin đêm theo vai trò:**

| Vai Trò | Biết gì |
|---------|---------|
| Morgan le Fey | Thấy tất cả đồng đội Ác có tên (Tay Sai, Minion) |
| Minion of Mordred | Thấy Morgan le Fey và các Minion khác |
| Cleric | Biết Người Lãnh Đạo đầu tiên thuộc phe nào |
| Arthur | Biết Morgan le Fey là ai |
| Blind Hunter | Không biết đồng đội, nhưng đồng đội biết họ qua ngón tay cái |
| Scion | Không biết ai, nhưng Morgan le Fey biết Scion |
| Changeling | Không biết ai và không ai biết họ |
| Troublemaker / Trickster | Không có thông tin đêm đặc biệt |

---

### Vòng Chơi

Mỗi vòng gồm các bước:

#### 1. Chọn Đội (Team Build)

- Bất kỳ người chơi nào cũng có thể đề xuất đội
- Đội phải có đúng số người theo bảng bên dưới
- Dùng: `/quest pick @p1 @p2 ...`

#### 2. Con Dấu Ma Thuật (Magic Seal)

- Đặt Con Dấu lên **một** thành viên trong đội
- Người bị phong ấn **buộc phải chơi Thành Công** (trừ một số vai đặc biệt)
- Dùng: `/quest seal @người`

#### 3. Bắt Đầu Nhiệm Vụ

- Dùng `/quest go` (nếu chưa chọn đội/dấu → tự động ngẫu nhiên)
- Hoặc `/quest autopick` để bot chọn ngẫu nhiên ngay

#### 4. Bỏ Phiếu Nhiệm Vụ (qua DM)

- Mỗi thành viên trong đội nhận **nút bỏ phiếu qua DM**
- Chọn ✅ **Thành Công** hoặc ❌ **Thất Bại**
- Kết quả được xáo trộn, công bố ở kênh chung (ẩn danh)

#### 5. Chọn Leader Tiếp Theo

- Sau mỗi nhiệm vụ, Leader hiện tại chọn người lãnh đạo kế tiếp
- Dùng: `/quest nextleader @người`
- ⛔ **Không được** chọn người đã từng làm Leader (có Veteran Token) hoặc người giữ Bùa Hộ Mệnh

---

### Bảng Kích Thước Đội

| Người chơi | NV1 | NV2 | NV3 | NV4 | NV5 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 2 | 3 | 2 | 3 | — |
| 5 | 2 | 3 | 2 | 3 | 3 |
| 6 | 2 | 3 | 4 | 3 | 4 |
| 7 | 2 | 3 | 3 | 4 | 4 |
| 8 | 3 | 4 | 4 | 5 | 5 |
| 9 | 3 | 4 | 4 | 5 | 5 |
| 10 | 3 | 4 | 4 | 5 | 5 |

> ⚠️ **Rule đặc biệt:** Trong game 7+ người, **Nhiệm Vụ 4 cần 2 thẻ Thất Bại** mới thua.
> ⚠️ Trong game **4 người**, chỉ cần **2 lần thất bại** là kết thúc (không có NV5).

---

### Bùa Hộ Mệnh (Amulet)

Xuất hiện sau một số nhiệm vụ nhất định (game từ 6+ người):

| Người chơi | Bùa xuất hiện sau nhiệm vụ |
|:---:|:---:|
| 4–5 | Không có |
| 6 | NV2 |
| 7 | NV2 và NV3 |
| 8–10 | NV2, NV3 và NV4 |

**Luồng Bùa:**

1. Leader trao Bùa cho 1 người: `/quest amulet @người`
2. Người giữ Bùa bí mật kiểm tra 1 người khác: `/quest check @người`   → Kết quả gửi qua DM (Thiện/Ác)
3. Leader chọn Leader tiếp theo: `/quest nextleader @người`
4. Tiến sang nhiệm vụ kế tiếp: `/quest advance`

> ⚠️ Người đã giữ Bùa không được làm Leader và không được giữ Bùa lần nữa.

---

### Nhiệm Vụ Cuối (khi Ác thắng 3 NV)

#### Giai Đoạn Thảo Luận (5 phút)

Tất cả thảo luận tự do. Phe Ác có thể nằm im, thừa nhận hoặc gây nhiễu.

#### Thợ Săn Mù — Cuộc Đi Săn

Nếu có **Blind Hunter** trong game, họ nhận DM và chọn:

- **Đi Săn**: Đặt tên đúng **2 người Thiện** theo **đúng vai trò** của họ → Ác thắng
- **Bỏ qua**: Chuyển sang Cơ Hội Cuối Cùng

Dùng: `/quest hunt <vai trò 1> @người1 <vai trò 2> @người2`

> **Quy tắc Arthur**: Nếu người được gọi tên **đầu tiên** là **Arthur** → Ác thắng ngay dù đúng hay sai.

#### Cơ Hội Cuối Cùng (Last Chance)

Mỗi người phe **Thiện** bí mật chỉ vào những kẻ mà họ nghi là Ác:

- Dùng: `/quest accuse @nghi_phạm1 @nghi_phạm2`
- Câu trả lời **ẩn** — chỉ tiết lộ sau khi **tất cả phe Thiện** đã bỏ phiếu
- Nếu **mọi người Thiện** cùng chỉ vào **đúng toàn bộ** kẻ Ác → **Thiện thắng**

---

## Vai Trò

### ⚔️ Phe Thiện

| Vai Trò | Mô Tả |
|---------|-------|
| **Loyal Servant of Arthur** | Luôn chơi Thành Công. Không có thông tin đặc biệt. |
| **Duke** | Trong Cơ Hội Cuối Cùng: chuyển hướng tay của một người sang mục tiêu khác. |
| **Archduke** | Tương tự Duke, có thể đổi bàn tay của một người trong Last Chance. |
| **Cleric** | Biết Leader đầu tiên thuộc phe nào. |
| **Youth** | Nếu bị Con Dấu Ma Thuật → **buộc phải chơi Thất Bại**. |
| **Troublemaker** | Khi bị kiểm tra lòng trung thành → **phải khai là Ác** (dù thực ra là Thiện). |
| **Apprentice** | Trong Last Chance: chỉ giơ 1 tay ban đầu; tay thứ 2 sau khi Ác hạ tay. |
| **Arthur** | Biết Morgan le Fey. Nếu Thợ Săn Mù gọi tên Arthur **đầu tiên** → Ác thắng ngay. |

### 💀 Phe Ác

| Vai Trò | Mô Tả |
|---------|-------|
| **Morgan le Fey** | Thấy các đồng đội Ác. Bỏ qua Con Dấu Ma Thuật — vẫn được chơi Thất Bại. |
| **Scion** | Không biết đồng đội Ác. Morgan le Fey biết Scion. Xuất hiện ở game 4–5 người. |
| **Minion of Mordred** | Biết Morgan le Fey và các Minion khác. |
| **Changeling** | Không biết và không ai biết. Xuất hiện từ 6 người. |
| **Blind Hunter** | Không biết đồng đội. Biết được qua ngón tay cái trong đêm. Có thể Đi Săn ở Final. |
| **Brute** | Chỉ được chơi Thất Bại ở NV1–3; bắt buộc Thành Công ở NV4–5. |
| **Lunatic** | Luôn phải chơi Thất Bại, trừ khi bị Con Dấu Ma Thuật. |
| **Mutineer** | Không biết đồng đội. Trong Last Chance, có thể không hạ tay. |
| **Trickster** | Khi bị kiểm tra → **có thể trả lời sai** (nói là Thiện dù thực ra là Ác). |
| **Revealer** | Biết đồng đội Ác. Sau lần thất bại thứ 3 → **phải lộ danh tính**. Không cần chỉ vào trong Last Chance. |

---

### Con Dấu Ma Thuật — Ngoại Lệ Theo Vai Trò

| Vai Trò | Hiệu ứng khi bị phong ấn |
|---------|--------------------------|
| Loyal Servant, Duke, Archduke, Apprentice | Phải chơi **Thành Công** |
| Youth | Phải chơi **Thất Bại** |
| Morgan le Fey | **Bỏ qua** — vẫn tự do chơi Thất Bại |
| Lunatic | Bị ghi đè — buộc chơi **Thành Công** |

---

## Lệnh Bot

| Lệnh | Mô Tả |
|------|-------|
| `/quest new` | Mở phòng chờ ở kênh này |
| `/quest join` | Tham gia phòng chờ |
| `/quest start` | Bắt đầu game (chỉ host) |
| `/quest pick @p1 @p2 ...` | Chọn đội (bất kỳ người chơi nào) |
| `/quest seal @người` | Đặt Con Dấu Ma Thuật |
| `/quest autopick` | Bot ngẫu nhiên chọn đội + dấu + bắt đầu ngay |
| `/quest go` | Bắt đầu nhiệm vụ (tự động pick nếu chưa chọn) |
| `/quest nextleader @người` | Chọn Leader tiếp theo (bắt buộc sau mỗi NV) |
| `/quest amulet @người` | Trao Bùa Hộ Mệnh |
| `/quest check @người` | Người giữ Bùa kiểm tra lòng trung thành |
| `/quest advance` | Tiến sang nhiệm vụ kế (sau giai đoạn Bùa) |
| `/quest accuse @p1 @p2` | Last Chance: chỉ 2 kẻ nghi là Ác (ẩn cho đến khi tất cả bỏ phiếu) |
| `/quest hunt <vai> @p1 <vai> @p2` | Thợ Săn Mù đi săn |
| `/quest status` | Xem trạng thái game |
| `/quest roles` | Xem danh sách vai trò |
| `/quest help` | Hướng dẫn nhanh |
| `/quest cancel` | Hủy game (chỉ host) |

---

## Cấu Trúc File

```
quest_bg/
├── bot.py          # Bot chính, tất cả slash commands
├── game_state.py   # State machine game theo từng kênh
├── roles.py        # Định nghĩa vai trò, bảng đội, bảng bùa
├── embeds.py       # Tạo Discord embed (Tiếng Việt)
├── views.py        # Button UI (bỏ phiếu, Đi Săn)
├── test_game.py    # Unit tests (29 tests, không cần Discord)
├── requirements.txt
├── .env.example
└── README.md
```

## Chạy Tests

```bash
python3 test_game.py
```
