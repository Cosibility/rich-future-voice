# Rich Future Voice

Rich Future Voice là bản giao diện riêng chạy trên Google Colab, phát triển từ dự án mã nguồn mở VoiceStudio.

## Chạy trên Google Colab

1. [Mở notebook Rich Future Voice trên Google Colab](https://colab.research.google.com/github/Cosibility/rich-future-voice/blob/main/notebooks/Rich_Future_Voice_Colab.ipynb).
2. Chọn `Runtime → Change runtime type → T4 GPU`.
3. Bấm **Run** một lần. Ô này tự clone `Cosibility/rich-future-voice`, cài môi trường, dựng giao diện voice cloning, tải model và khởi động backend.
4. Khi hoàn tất, bấm nút **MỞ RICH FUTURE VOICE** để mở ứng dụng trong tab mới. Nếu trình duyệt chặn tab, bấm lại nút hoặc sao chép URL hiển thị ngay bên dưới nút.

Lần chạy đầu thường mất 5–10 phút để cài thư viện; model giọng nói cần tải thêm vài GB. Dữ liệu trong `/content` sẽ mất khi phiên Colab kết thúc.

## Tạo và tải giọng nói

1. Tải lên hoặc thu một đoạn giọng mẫu sạch dài khoảng 5–15 giây.
2. Nhập nội dung cần đọc và chọn ngôn ngữ.
3. Chọn chất lượng: **Nhanh** (8 bước, dùng để thử), **Cân bằng** (16 bước, mặc định) hoặc **Studio** (32 bước, ưu tiên chất lượng).
4. Chọn tốc độ **0.85× / 1× / 1.15×** rồi bấm **Tổng hợp âm thanh**.
5. Sau khi hoàn tất, tải file WAV gốc hoặc MP3 192 kbps. Năm bản gần nhất có thể được nghe lại, tải xuống hoặc xóa trong bảng **Lịch sử**.
6. Để sửa tên riêng hoặc thương hiệu bị đọc sai, thêm cặp **từ gốc → cách đọc** trong bảng **Từ điển phát âm**. Mục sửa được áp dụng cho ngôn ngữ đang chọn.

Launcher tự làm nóng model ở chế độ nền ngay khi ứng dụng sẵn sàng, vì vậy thời gian nạp model đầu tiên thường diễn ra trong lúc người dùng chuẩn bị giọng mẫu và kịch bản. Thời gian dựng thực tế vẫn phụ thuộc độ dài văn bản, chất lượng đã chọn và GPU Colab được cấp.

## Khóa dependency

- Python được cài đúng theo `uv.lock` bằng `uv sync --frozen --no-dev`; launcher từ chối tự resolve hoặc sửa lockfile.
- Công cụ `uv` và Bun đều được khóa phiên bản trong launcher.
- Frontend được cài bằng `bun install --frozen-lockfile` và các dependency chuyển tiếp có advisory được ép về bản vá đã kiểm tra trong `package.json`.
- Model mặc định tiếp tục được tải bằng commit revision cố định, không chạy tùy ý bản mới nhất.

## Mô hình nhiều người dùng

Notebook này dành cho mô hình **mỗi người một phiên Colab riêng**:

1. Chia sẻ liên kết notebook, không chia sẻ URL ứng dụng được tạo sau khi chạy.
2. Mỗi người chọn **Copy to Drive** hoặc chạy notebook bằng chính tài khoản Google của họ.
3. Mỗi tài khoản nhận một máy ảo, thư mục dữ liệu và URL proxy Colab riêng.
4. Không dùng Cloudflare Tunnel, ngrok hoặc công khai cổng backend.

Không dùng một phiên Colab/URL chung cho nhiều người. Backend hiện không có tài khoản người dùng hay vùng dữ liệu tách biệt; dùng chung một phiên có thể làm lộ mẫu giọng và lịch sử tạo âm thanh giữa những người truy cập.

Trước mỗi đợt phát hành công khai, hãy khóa notebook vào một commit hoặc tag đã kiểm tra thay vì để nó tự động chạy mã mới nhất từ `main`.

## Nhận diện Rich Future

- Tên sản phẩm: **Rich Future Voice**
- Phong cách: nền xanh đen, điểm nhấn xanh ngọc và xanh cyan
- Logo: tín hiệu giọng nói đang tăng trưởng, gợi liên tưởng đến “future”
- Giao diện Colab chỉ giữ luồng tải/thu giọng mẫu, nhập nội dung, chọn ngôn ngữ và tạo âm thanh
- Giao diện có ba preset chất lượng, ba preset tốc độ, năm bản gần nhất, sửa phát âm và tải WAV/MP3
- Giao diện mặc định: tiếng Việt theo ngôn ngữ trình duyệt, vẫn hỗ trợ các ngôn ngữ có sẵn của dự án gốc
- Chế độ Colab ẩn các liên kết cập nhật, báo lỗi, Discord, tài trợ và giấy phép thương mại của dự án gốc
- Mục Giới thiệu chỉ để lại liên kết **Mã nguồn** trỏ về repository Rich Future, nhằm đáp ứng nghĩa vụ AGPL mà không đưa thương hiệu gốc vào luồng sử dụng chính

## Giấy phép và nguồn gốc

Dự án gốc VoiceStudio dùng giấy phép AGPL-3.0. Khi cung cấp bản Rich Future Voice đã sửa đổi qua mạng, bạn phải cung cấp mã nguồn tương ứng theo cùng giấy phép, trừ khi có thỏa thuận giấy phép thương mại riêng với tác giả dự án gốc. Giữ nguyên `LICENSE` và các thông báo bản quyền trong repository.

Nguồn dự án gốc: https://github.com/debpalash/VoiceStudio
