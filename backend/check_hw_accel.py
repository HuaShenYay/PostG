import torch

print(f"Torch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

try:
    import intel_extension_for_pytorch as ipex
    print("IPEX installed.")
    try:
        print(f"XPU Available: {torch.xpu.is_available()}")
    except Exception as e:
        print(f"XPU detection failed: {e}")
except ImportError:
    print("IPEX not installed.")

try:
    import torch_directml
    print("DirectML installed.")
    dml = torch_directml.device()
    print(f"DirectML Device: {dml}")
except ImportError:
    print("DirectML not installed.")

# Check for OpenVINO as it's great for Intel Xe
try:
    from openvino.runtime import Core
    core = Core()
    devices = core.available_devices
    print(f"OpenVINO Devices: {devices}")
except ImportError:
    print("OpenVINO not installed.")
