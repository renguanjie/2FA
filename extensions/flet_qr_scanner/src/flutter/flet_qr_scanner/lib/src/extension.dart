import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'flet_qr_scanner.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "FletQrScanner":
        return FletQrScannerControl(control: control);
      default:
        return null;
    }
  }
}
