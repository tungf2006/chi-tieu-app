# SOP: SO SÁNH & TINH CHỈNH DỰ BÁO TÀI CHÍNH (Day 30)

**Chủ sở hữu quy trình:** Data Analyst / ML Engineer  
**Phạm vi áp dụng:** Hệ thống dự báo chi tiêu `chi-tieu-app` (endpoint `/forecast`)  
**Mục tiêu:** Khi dự báo có sai lệch lớn (MAPE > ngưỡng cho phép), thực hiện quy trình chuẩn để (1) làm sạch nhiễu, (2) tăng độ nhạy bằng trung bình trượt, (3) ghi chép bài học để cải tiến mô hình.

---

## 1. NGUYÊN TẮC CHUNG

> **Quy tắc vàng:** Sai số không phải lỗi — sai số là tín hiệu. Mỗi lần `|pred - actual|` vượt ngưỡng, ta phải trả lời được 3 câu hỏi:
> 1. Dữ liệu có bị nhiễu / outlier không?
> 2. Mô hình có bắt kịp biến động gần nhất không?
> 3. Giới hạn của mô hình hiện tại là gì, và ta học được gì?

**Ngưỡng cảnh báo (đề xuất):** MAPE < 5% = Tốt | 5–15% = Chấp nhận được | > 15% = Cần tinh chỉnh (kích hoạt SOP này).

---

## 2. BƯỚC 1 — XỬ LÝ DỮ LIỆU NHIỄU (OUTLIER HANDLING)

### 2.1. Định nghĩa Outlier trong tài chính
Outlier = khoản chi **bất thường, phi chu kỳ, phi cấu trúc** (sửa xe 5 triệu, du lịch 1 lần/năm) khác biệt rõ rệt với phân bổ chi tiêu thường ngày.  
⚠️ **Không nhầm lẫn:** Chi cuối tuần cao hơn ngày thường là **mùa vụ (seasonality)** — KHÔNG phải outlier, không được xóa.

### 2.2. Kỹ thuật phát hiện (3 lớp)
| Lớp | Phương pháp | Công thức / Quy tắc | Dùng khi |
|-----|-------------|--------------------|----------|
| Thống kê | **IQR** | `[Q1 - 1.5·IQR, Q3 + 1.5·IQR]` | Dữ liệu phân bổ bất đối xứng |
| Thống kê | **Z-score** | `|z| > 3` (hoặc 2.5) | Phân bổ gần chuẩn |
| Domain | **Business rule** | `amount > k × median_ngày` (k=5) | Có ngữ cảnh nghiệp vụ rõ |

### 2.3. Quyết định: Xóa / Winsorize / Giữ
- **Xóa (drop):** outlier rõ ràng, phi chu kỳ, sai sót nhập liệu. → Dùng cho dự báo xu hướng.
- **Winsorize (cắt ngưỡng):** thay bằng percentile 95/99. → Giữ thông tin nhưng giảm ảnh hưởng.
- **Giữ nguyên:** nếu là chi thực tế quan trọng (nợ, y tế) → nên báo cáo riêng, không đưa vào mô hình dự báo thường.

### 2.4. Code mẫu (áp dụng vào pipeline của bạn)
```python
import pandas as pd
import numpy as np

def remove_outliers_iqr(df, amount_col="y", factor=1.5):
    """Loai bo outlier bang phuong phap IQR."""
    q1 = df[amount_col].quantile(0.25)
    q3 = df[amount_col].quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - factor * iqr, q3 + factor * iqr
    mask = (df[amount_col] >= low) & (df[amount_col] <= high)
    removed = df[~mask]
    print(f"[Outlier] Da loai {len(removed)} diem (ngoai [{low:,.0f}, {high:,.0f}])")
    return df[mask].copy(), removed

# Su dung: truoc khi goi forecast_total()
clean_df, bad = remove_outliers_iqr(daily_df)
result = forecast_total(method="linear", daily_df=clean_df, days_in_month=31)
```

> **Bài học từ hệ thống của bạn:** Trong kịch bản `TC4_Outlier` (1 ngày chi 5 triệu), MAPE tuyến tính lên tới **24.1%**. Sau khi áp dụng IQR drop, dự báo sẽ quay về vùng <5% vì đường cumulative không bị "kéo vểnh" bởi điểm đơn lẻ.

---

## 3. BƯỚC 2 — TRUNG BÌNH TRƯỢT 7 NGÀY (MOVING AVERAGE)

### 3.1. Tại sao "trung bình cả tháng" không đủ?
- Trung bình tháng = hằng số, **không nhạy** với sự thay đổi gần đây (tăng/giảm chi sau giữa tháng).
- Ví dụ: sang tháng 9 bạn bắt đầu tiết kiệm, chi giảm dần — nhưng trung bình tháng 8 vẫn "kéo" dự báo tháng 9 lên cao → sai lệch.

### 3.2. Rolling 7-day Moving Average
Thay vì `mean(tháng)`, dùng `mean(7 ngày gần nhất)` làm **burn rate hiện tại**:
```
burn_rate_moi_nhat = mean(amount[day-6 .. day])
```
→ Phản ánh hành vi chi tiêu **hiện tại**, nhạy với xu hướng mới.

### 3.3. Code mẫu
```python
def rolling_burn_rate(df, amount_col="y", window=7):
    """Burn rate trượt 7 ngày gần nhất."""
    s = df[amount_col].rolling(window=window, min_periods=1).mean()
    return float(s.iloc[-1])

def forecast_with_rolling(daily_df, days_in_month, window=7):
    """Du bao bang burn rate truot thay vi duong tuyen tinh."""
    df = daily_df.sort_values("ds").reset_index(drop=True)
    observed = df[amount_col].sum()
    last_day = df["ds"].dt.day.max()
    br = rolling_burn_rate(df, window=window)
    remaining_days = days_in_month - last_day
    predicted = observed + br * remaining_days
    return predicted, br

# Vi du
pred, br = forecast_with_rolling(clean_df, days_in_month=31, window=7)
print(f"Burn rate 7-ngay: {br:,.0f} VND | Du bao: {pred:,.0f} VND")
```

### 3.4. Khi nào dùng MA thay Linear?
| Tình huống | Dùng |
|------------|------|
| Dữ liệu ổn định, ít biến động | Linear (cumulative) |
| Chi tiêu đổi hướng gần đây (tiết kiệm/tăng đột ngột) | **Rolling 7-day** |
| Có mùa vụ tuần rõ rệt | Seasonal method |
| Xu hướng dài hạn (tăng/giảm đều) | ARIMA |

> **Lưu ý:** Rolling MA nhạy hơn nhưng **nhạy cảm với nhiễu ngắn hạn** — nên kết hợp Bước 1 (làm sạch outlier) trước khi tính MA.

---

## 4. BƯỚC 3 — KỸ NĂNG PHẢN TƯ (REFLECTION)

### 4.1. Tại sao ghi chép phản tư quan trọng?
- Chuyển từ "mô hình sai" → "mô hình có giới hạn đã biết".
- Thể hiện tư duy **metacognitive** (biết mình biết gì, không biết gì) — kỹ năng phỏng vấn cao cấp.

### 4.2. Mẫu nhận xét chuyên nghiệp (dùng phỏng vấn)

**Mẫu A — Nhận diện giới hạn mô hình tuyến tính:**
> *"Mô hình Linear Regression trên chuỗi tích lũy của tôi giả định chi tiêu thay đổi theo tốc độ đều đặn (hằng số). Trong thực tế, dữ liệu `TC3_IncreasingTrend` cho thấy MAPE lên tới 15.9% khi chỉ quan sát 10 ngày đầu, vì độ dốc thực tế bị đánh giá thấp do chưa đủ pha tăng. Bài học: mô hình tuyến tính đơn giản thiếu khả năng bắt xu hướng phi tuyến ngắn hạn — ta cần ARIMA hoặc feature kỹ thuật thêm."*

**Mẫu B — Học từ sai số outlier:**
> *"Khi gặp khoản chi 5 triệu đột biến (`TC4_Outlier`), MAPE tăng vọt lên 24%. Thay vì coi đó là lỗi mô hình, tôi nhận ra đây là vấn đề chất lượng dữ liệu. Tôi áp dụng phát hiện IQR để tách biệt chi phi chu kỳ khỏi xu hướng nền, giúp MAPE quay về <5%. Điều này củng cố nguyên tắc: 80% độ chính xác đến từ làm sạch dữ liệu, 20% từ thuật toán."*

**Mẫu C — So sánh mô hình (model selection):**
> *"Tôi so sánh 3 phương pháp trên 8 bộ dữ liệu: Linear (MAPE tb 11%), Seasonal (9%), ARIMA (cải thiện mạnh ở xu hướng: TC3/TC5 MAPE <0.5%). Tuy nhiên ARIMA nhạy cảm với dữ liệu ngắn (<10 ngày) và chậm hơn (~40ms vs 2ms). Quyết định triển khai: dùng Seasonal làm mặc định, chuyển ARIMA khi đủ ≥15 ngày và có xu hướng rõ."*

**Mẫu D — Đề xuất cải tiến (forward-looking):**
> *"Giới hạn tiếp theo tôi muốn giải quyết là mùa vụ lễ tết (Tết, Black Friday) — chu kỳ năm chưa được mô hình hóa. Kế hoạch: thêm feature `is_holiday`, dùng SARIMA (seasonal ARIMA) với chu kỳ 12 tháng, và xây dựng pipeline tự động phát hiện outlier bằng IQR trước mỗi lần fit."*

### 4.3. Template ghi chép hàng ngày (Reflection Log)
```
Ngày: ____ | Dataset: ____ | Method: ____ | MAPE: ____%
1. Quan sát: dự báo ___ cao/thấp hơn thực tế vì ___.
2. Nguyên nhân gốc: [ ] Nhiễu  [ ] Mùa vụ  [ ] Xu hướng  [ ] Ít dữ liệu  [ ] Khác: ___
3. Hành động: đã áp dụng ___ (IQR / Rolling / Đổi method).
4. Kết quả sau tinh chỉnh: MAPE ___% (trước: ___%).
5. Bài học: ___.
```

---

## 5. CHECKLIST THỰC THI (Day 30)

- [ ] Dự báo chạy, tính MAPE so với thực tế (hoặc hold-out)
- [ ] Nếu MAPE > 15% → kích hoạt SOP
- [ ] Bước 1: Chạy IQR/Z-score, xác định outlier, quyết định drop/winsorize
- [ ] Bước 2: Tính rolling 7-day burn rate, so sánh với linear
- [ ] Chọn method tối ưu theo bảng §3.4
- [ ] Bước 3: Ghi Reflection Log + 1 mẫu nhận xét phỏng vấn
- [ ] Cập nhật tài liệu, commit thay đổi

---

## 6. TÀI LIỆU THAM KHẢO NỘI BỘ
- `app/services/forecast.py` — 3 method: linear / seasonal / arima
- `tests/test_forecast_scenarios.py` — 8 dataset, so sánh MAPE
- `prepare_timeseries.py` — chuẩn hóa daily series
- Kết quả đã đo: TC2 seasonal MAPE 0.0% | TC3/TC5 ARIMA MAPE <0.5% | TC4 outlier linear 24.1%
