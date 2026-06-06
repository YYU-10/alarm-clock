from flask import Flask, render_template, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory storage
devices = []
borrowings = []


def init_sample_data():
    """Initialize with sample devices."""
    samples = [
        {"name": "数字示波器", "type": "测量仪器", "stock": 3, "description": "带宽100MHz，4通道，适用于电路信号分析"},
        {"name": "高速离心机", "type": "实验设备", "stock": 2, "description": "最高转速15000rpm，适用于样品分离"},
        {"name": "光谱分析仪", "type": "分析仪器", "stock": 1, "description": "波长范围200-1100nm，用于光谱测量"},
        {"name": "3D打印机", "type": "制造设备", "stock": 2, "description": "FDM技术，打印精度0.1mm，最大尺寸300x300x400mm"},
        {"name": "万用表", "type": "测量仪器", "stock": 10, "description": "高精度数字万用表，支持电压/电流/电阻测量"},
    ]
    for s in samples:
        devices.append({
            "id": str(uuid.uuid4()),
            "name": s["name"],
            "type": s["type"],
            "stock": s["stock"],
            "description": s["description"],
        })


init_sample_data()


def get_overlapping_borrowings(device_id, start_time, end_time, exclude_id=None):
    """Find the maximum number of concurrent borrowings within the given time range."""
    req_start = datetime.fromisoformat(start_time)
    req_end = datetime.fromisoformat(end_time)

    overlapping = []
    for b in borrowings:
        if b["device_id"] != device_id:
            continue
        if b["status"] != "active":
            continue
        if exclude_id and b["id"] == exclude_id:
            continue
        b_start = datetime.fromisoformat(b["start_time"])
        b_end = datetime.fromisoformat(b["end_time"])
        if req_start < b_end and req_end > b_start:
            overlapping.append((b_start, b_end))

    if not overlapping:
        return 0

    events = []
    for (s, e) in overlapping:
        events.append((s, 1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], x[1]))

    max_concurrent = 0
    current = 0
    for _, delta in events:
        current += delta
        if current > max_concurrent:
            max_concurrent = current
    return max_concurrent


def get_current_borrowed_count(device_id):
    """Get number of active borrowings for a device (currently in use or future reserved)."""
    now = datetime.now()
    count = 0
    for b in borrowings:
        if b["device_id"] != device_id or b["status"] != "active":
            continue
        b_end = datetime.fromisoformat(b["end_time"])
        if b_end > now:
            count += 1
    return count


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/devices", methods=["GET"])
def list_devices():
    result = []
    for d in devices:
        borrowed = get_current_borrowed_count(d["id"])
        result.append({
            **d,
            "borrowed": borrowed,
            "available": d["stock"] - borrowed,
        })
    return jsonify(result)


@app.route("/api/devices", methods=["POST"])
def add_device():
    data = request.json
    if not data.get("name") or not data.get("type") or data.get("stock") is None:
        return jsonify({"error": "设备名称、类型和库存数量为必填项"}), 400
    if int(data["stock"]) < 1:
        return jsonify({"error": "库存数量必须大于0"}), 400
    device = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "type": data["type"],
        "stock": int(data["stock"]),
        "description": data.get("description", ""),
    }
    devices.append(device)
    return jsonify(device), 201


@app.route("/api/devices/<device_id>", methods=["PUT"])
def update_device(device_id):
    data = request.json
    for d in devices:
        if d["id"] == device_id:
            if data.get("name"):
                d["name"] = data["name"]
            if data.get("type"):
                d["type"] = data["type"]
            if data.get("stock") is not None:
                d["stock"] = int(data["stock"])
            if "description" in data:
                d["description"] = data["description"]
            return jsonify(d)
    return jsonify({"error": "设备不存在"}), 404


@app.route("/api/devices/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    global devices
    active = [b for b in borrowings if b["device_id"] == device_id and b["status"] == "active"]
    if active:
        return jsonify({"error": "该设备有未归还的借用记录，无法删除"}), 400
    devices = [d for d in devices if d["id"] != device_id]
    return jsonify({"message": "删除成功"})


@app.route("/api/borrowings", methods=["GET"])
def list_borrowings():
    result = []
    for b in borrowings:
        device = next((d for d in devices if d["id"] == b["device_id"]), None)
        result.append({
            **b,
            "device_name": device["name"] if device else "已删除设备",
        })
    return jsonify(sorted(result, key=lambda x: x["created_at"], reverse=True))


@app.route("/api/borrowings", methods=["POST"])
def add_borrowing():
    data = request.json
    if not data.get("device_id") or not data.get("borrower") or not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "设备、负责人和借用时间为必填项"}), 400

    device = next((d for d in devices if d["id"] == data["device_id"]), None)
    if not device:
        return jsonify({"error": "设备不存在"}), 404

    try:
        start = datetime.fromisoformat(data["start_time"])
        end = datetime.fromisoformat(data["end_time"])
    except ValueError:
        return jsonify({"error": "时间格式错误"}), 400

    if end <= start:
        return jsonify({"error": "结束时间必须晚于开始时间"}), 400

    overlap_count = get_overlapping_borrowings(data["device_id"], data["start_time"], data["end_time"])
    if overlap_count >= device["stock"]:
        device_name = device["name"]
        stock = device["stock"]
        return jsonify({
            "error": "时间冲突：该时间段内「{}」已全部被借出（库存{}台，已借{}台）".format(device_name, stock, overlap_count)
        }), 409

    borrowing = {
        "id": str(uuid.uuid4()),
        "device_id": data["device_id"],
        "borrower": data["borrower"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    borrowings.append(borrowing)
    return jsonify(borrowing), 201


@app.route("/api/borrowings/<borrowing_id>/return", methods=["POST"])
def return_device(borrowing_id):
    for b in borrowings:
        if b["id"] == borrowing_id:
            if b["status"] != "active":
                return jsonify({"error": "该记录已归还"}), 400
            b["status"] = "returned"
            b["returned_at"] = datetime.now().isoformat()
            return jsonify(b)
    return jsonify({"error": "借用记录不存在"}), 404


@app.route("/api/stats", methods=["GET"])
def get_stats():
    total_devices = len(devices)
    total_stock = sum(d["stock"] for d in devices)
    active_borrowings = sum(1 for b in borrowings if b["status"] == "active")
    total_borrowed = get_total_currently_borrowed()
    return jsonify({
        "total_devices": total_devices,
        "total_stock": total_stock,
        "active_borrowings": active_borrowings,
        "total_borrowed": total_borrowed,
    })


def get_total_currently_borrowed():
    now = datetime.now()
    count = 0
    for b in borrowings:
        if b["status"] != "active":
            continue
        b_end = datetime.fromisoformat(b["end_time"])
        if b_end > now:
            count += 1
    return count


if __name__ == "__main__":
    app.run(debug=True, port=5000)
