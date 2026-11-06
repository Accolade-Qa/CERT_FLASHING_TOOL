# Service Tool

## Project layout

- `service_tool.py` is the application's single root entry point and is used by `deploy.bat`.
- `service_tool_app\ui.py` contains the Qt interface.
- `service_tool_app\device.py` contains serial communication, the certificate flow, and result persistence.
- `service_tool_app\config.py` owns application/resource paths and shared constants.
- `service_tool_app\logic.py` contains pure Python device-logic helpers.
- `resources\` contains the Qt form, certificates, and logo.

## Run the application

Install the packages in `requirements.txt`, then run:

```powershell
python service_tool.py
```

## Tests

```powershell
python -m unittest discover -s tests
```
