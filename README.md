# A box demo
Python SDK + PyTeal come together to make some 🎁📦.

### Installation

Boxes require PyTeal 0.21.0+ and Algorand's Python SDK 2.0.0+.

```
pip install -r requirements.txt
```

### Demo

Uses [sandbox](https://github.com/algorand/sandbox) in dev mode:

```
./sandbox up dev
python box-demo.py # This will create the TEAL program: approve-box.teal
python deploy_box.py
```
