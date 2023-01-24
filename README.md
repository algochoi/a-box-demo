# A box demo
Python SDK + PyTeal come together to make some 🎁📦.

### Installation

Boxes require PyTeal 0.20.1+ and Algorand's Python SDK 1.20.1+.

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
