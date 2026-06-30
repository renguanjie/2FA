# Introduction

FletQrScanner for Flet.

## Examples

```
import flet as ft

from flet_qr_scanner import FletQrScanner


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=FletQrScanner(
                    tooltip="My new FletQrScanner Control tooltip",
                    value = "My new FletQrScanner Flet Control",
                ),),

    )


ft.run(main)
```

## Classes

[FletQrScanner](FletQrScanner.md)
