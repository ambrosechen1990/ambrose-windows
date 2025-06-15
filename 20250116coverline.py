import cv2
import os
from datetime import datetime
from tkinter import Tk, filedialog, Button, Label, Entry, Frame
import numpy as np
import logging
import atexit

# 固定视频帧大小和默认轨迹线宽度
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TRACK_WIDTH = 15  # 默认轨迹线宽度

# 设置日志文件夹路径
LOG_DIR = r"D:\py\project\trajectory line\log"
os.makedirs(LOG_DIR, exist_ok=True)

# 设置日志文件名称和路径
log_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_file_path = os.path.join(LOG_DIR, log_file_name)

# 配置日志记录
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
atexit.register(logging.shutdown)  # 确保程序退出前刷新日志缓冲区

def log_exception(ex):
    """记录异常信息到日志文件"""
    logging.error("程序运行时出现异常", exc_info=ex)

def create_tracker():
    if hasattr(cv2, 'legacy') and hasattr(cv2.legacy, 'TrackerCSRT_create'):
        return cv2.legacy.TrackerCSRT_create()
    elif hasattr(cv2, 'TrackerCSRT_create'):
        return cv2.TrackerCSRT_create()
    else:
        raise AttributeError("你的OpenCV没有CSRT跟踪器，请安装opencv-contrib-python")

def process_video(video_path, track_width):
    frame_count = 0
    coverage_rate = 0
    if not os.path.exists(video_path):
        print(f"视频文件 {video_path} 不存在")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件 {video_path}")
        return

    ret, frame = cap.read()
    if not ret:
        print("无法读取视频文件")
        return

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    tracker = None
    init_box = None
    all_track_points = []
    current_track_points = []

    polygon_points = []  # 存储多边形的点
    drawing_polygon = True  # 标记是否在绘制多边形

    def on_mouse(event, x, y, flags, param):
        nonlocal drawing_polygon
        if drawing_polygon:
            if event == cv2.EVENT_LBUTTONDOWN:
                polygon_points.append((x, y))
            elif event == cv2.EVENT_RBUTTONDOWN and len(polygon_points) > 2:
                # 右键点击完成闭环
                drawing_polygon = False

    cv2.namedWindow("Tracking")
    cv2.setMouseCallback("Tracking", on_mouse)

    # 绘制多边形区域
    while drawing_polygon:
        temp_frame = frame.copy()
        if len(polygon_points) > 1:
            for i in range(1, len(polygon_points)):
                cv2.line(temp_frame, polygon_points[i - 1], polygon_points[i], (0, 255, 255), 2)
            if len(polygon_points) > 2:
                cv2.line(temp_frame, polygon_points[-1], polygon_points[0], (0, 255, 255), 2)

        cv2.imshow("Tracking", temp_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and len(polygon_points) > 2:
            drawing_polygon = False

    # 创建多边形掩码
    mask = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(polygon_points, np.int32)], 255)
    polygon_area = cv2.countNonZero(mask)

    # 找到多边形的轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 获取多边形内的所有点
    points_inside_polygon = []
    for y in range(FRAME_HEIGHT):
        for x in range(FRAME_WIDTH):
            if cv2.pointPolygonTest(contours[0], (x, y), False) >= 0:
                points_inside_polygon.append((x, y))

    white_trail = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)

    while True:
        frame_count += 1
        if not ret:
            print("视频播放完毕或读取失败")
            break

        overlay = frame.copy()
        # overlay = mask

        # 显示多边形区域
        cv2.polylines(overlay, [np.array(polygon_points, np.int32)], isClosed=True, color=(0, 255, 255), thickness=2)

        # 绘制轨迹线（透明绿色）
        for i in range(1, len(all_track_points)):
            if all_track_points[i - 1] and all_track_points[i]:
                cv2.line(overlay, all_track_points[i - 1], all_track_points[i], (0, 255, 0), track_width)
                cv2.line(white_trail, all_track_points[i - 1], all_track_points[i], (127, 127, 127), max(1, track_width // 4))

        # 叠加白色轨迹层
        track_overlay = cv2.add(overlay, white_trail)

        # 显示覆盖率
        # covered_area = 0
        # for point in all_track_points:
        #     if mask[point[1], point[0]] == 255:
        #         covered_area += 1
        #     else:
        #         print(point[1], point[0] ,mask[point[1], point[0]])
        #         # assert False
        if frame_count % 20 == 0:
            # green_mask = np.all(points_inside_polygon == pure_green, axis=-1)
            # covered_area = np.sum(green_mask)
            covered_area = 0
            for point in points_inside_polygon:
                x, y = point
                if overlay[y, x][1] == 255 and overlay[y, x][0] == 0  and overlay[y, x][2] == 0:  # 检查绿色通道的值
                    covered_area += 1
            coverage_rate = (covered_area / polygon_area) * 100 if polygon_area > 0 else 0
        cv2.putText(overlay, f"Coverage: {coverage_rate:.2f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 139, 255), 2)
        # 显示进度条
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        progress = current_frame / total_frames if total_frames > 0 else 0

        progress_bar_width = int(FRAME_WIDTH * progress)
        progress_background_color = (50, 50, 50)
        progress_bar_color = (0, 255, 0)

        cv2.rectangle(overlay, (0, FRAME_HEIGHT - 10), (FRAME_WIDTH, FRAME_HEIGHT), progress_background_color, -1)
        cv2.rectangle(overlay, (0, FRAME_HEIGHT - 10), (progress_bar_width, FRAME_HEIGHT), progress_bar_color, -1)

        # 显示结果帧
        alpha = 0.3
        result_frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        result_track_frame = cv2.addWeighted(track_overlay, alpha, frame, 1 - alpha, 0)
        cv2.imshow("Coverage", result_frame)
        cv2.imshow("Tracking", result_track_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            init_box = cv2.selectROI("Select object", frame, fromCenter=False)
            if any(init_box):
                tracker = create_tracker()
                tracker.init(frame, init_box)
                current_track_points = []
                all_track_points.extend(current_track_points)
            cv2.destroyWindow("Select object")

        if tracker:
            success, bbox = tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in bbox]
                center_point = (int(x + w / 2), int(y + h / 2))
                current_track_points.append(center_point)
                all_track_points.append(center_point)
            else:
                tracker = None

        # 读取下一帧
        # last_frame = frame.copy()
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    cap.release()
    cv2.destroyAllWindows()

    # 保存最后一帧带有轨迹线和覆盖率的图像
    output_dir = r"D:\py\project\trajectory line\picture"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"Coverage_rate_{timestamp}.png")

    cv2.imwrite(output_path, result_frame)  # 保存带轨迹线的最后显示帧
    print(f"图像已保存至 {output_path}")


def select_video():
    video_path = filedialog.askopenfilename(
        title="选择视频文件",
        filetypes=[("视频文件", "*.mp4;*.avi;*.mov;*.mkv")])
    if video_path:
        process_video(video_path, TRACK_WIDTH)


def update_track_width():
    global TRACK_WIDTH
    try:
        TRACK_WIDTH = max(1, int(track_width_entry.get()))
    except ValueError:
        print("请输入一个有效的整数")


def confirm_changes():
    update_track_width()


# GUI 部分
root = Tk()
root.title("视频轨迹工具")
root.geometry("400x200")

Label(root, text="请选择一个视频文件:").pack(pady=10)
Button(root, text="选择视频", command=select_video).pack(pady=10)

frame_controls = Frame(root)
frame_controls.pack(pady=10)

track_width_label = Label(frame_controls, text="轨迹线宽度:")
track_width_label.pack(side="left", padx=10)

track_width_entry = Entry(frame_controls)
track_width_entry.insert(0, str(TRACK_WIDTH))
track_width_entry.pack(side="left")

confirm_button = Button(frame_controls, text="确定", command=confirm_changes)
confirm_button.pack(side="left", padx=10)

root.mainloop()
