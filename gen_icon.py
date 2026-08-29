"""
Tạo icon đơn giản cho app (chạy 1 lần lúc build, không cần chạy khi dùng app
bình thường). Dùng cùng bảng màu với giao diện web (nền navy đậm, chữ V amber).
"""
from PIL import Image, ImageDraw, ImageFont

NAVY = (20, 20, 28, 255)
AMBER = (232, 163, 61, 255)
AMBER_DARK = (201, 127, 34, 255)

SIZE = 256


def build_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Nền bo góc màu navy
    radius = 48
    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=NAVY)

    # Hình thoi/mũi tên gradient-giả kiểu "translate" bằng 2 tam giác chồng màu amber
    cx, cy = SIZE // 2, SIZE // 2
    r = 78
    draw.polygon(
        [(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)],
        fill=AMBER,
    )
    draw.polygon(
        [(cx - r * 0.45, cy), (cx, cy - r * 0.45), (cx + r * 0.45, cy), (cx, cy + r * 0.45)],
        fill=NAVY,
    )

    return img


def main():
    img = build_icon()
    img.save("assets/icon.png")

    # .ico cần nhiều kích thước khác nhau để Windows hiển thị đẹp ở mọi nơi
    # (taskbar, desktop, file explorer...)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("assets/icon.ico", format="ICO", sizes=sizes)
    print("Đã tạo assets/icon.png và assets/icon.ico")


if __name__ == "__main__":
    main()
