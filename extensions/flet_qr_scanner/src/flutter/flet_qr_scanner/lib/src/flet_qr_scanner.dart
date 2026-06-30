import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

/// Flet control that wraps the native [MobileScanner] (CameraX/ML Kit on
/// Android, AVFoundation/Vision on iOS) and forwards decoded QR values to
/// Python through the "detect" event.
class FletQrScannerControl extends StatefulWidget {
  final Control control;

  const FletQrScannerControl({
    super.key,
    required this.control,
  });

  @override
  State<FletQrScannerControl> createState() => _FletQrScannerControlState();
}

class _FletQrScannerControlState extends State<FletQrScannerControl> {
  late final MobileScannerController _controller;
  String? _lastValue;

  @override
  void initState() {
    super.initState();
    final facing = widget.control.getString("facing", "back")!;
    _controller = MobileScannerController(
      facing: facing == "front" ? CameraFacing.front : CameraFacing.back,
      torchEnabled: widget.control.getBool("torch", false)!,
      formats: const [BarcodeFormat.qrCode],
    );
  }

  @override
  void didUpdateWidget(covariant FletQrScannerControl oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Apply torch on/off changes coming from Python.
    final wantTorch = widget.control.getBool("torch", false)!;
    final torchOn = _controller.value.torchState == TorchState.on;
    if (wantTorch != torchOn) {
      _controller.toggleTorch();
    }
  }

  void _onDetect(BarcodeCapture capture) {
    for (final barcode in capture.barcodes) {
      final value = barcode.rawValue;
      if (value != null && value.isNotEmpty && value != _lastValue) {
        _lastValue = value;
        widget.control.triggerEvent("detect", value);
        break;
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scanner = MobileScanner(
      controller: _controller,
      onDetect: _onDetect,
      errorBuilder: (context, error, child) => Center(
        child: Text(
          "Camera error: ${error.errorCode}",
          style: const TextStyle(color: Colors.white),
        ),
      ),
    );

    return LayoutControl(control: widget.control, child: scanner);
  }
}
