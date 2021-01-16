# karen

![Karen Logo](https://vignette.wikia.nocookie.net/spongebob/images/1/18/Karen-blue-form-stock-art.png/revision/latest?cb=20200317150606)

:warning: I took Karen down following the end of the 2020 Fantasy season, but she'll be back next year!

# Developer Set up

Install the dependencies with:

```bash
pip install --upgrade -r requirements.txt
```

Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

Start the local Streamlit server with:

```bash
streamlit run app.py
```

## Potential issues:

When installing streamlit, the `watchdog` installation might fail. If this is
the case, make sure to run:
```bash
rm -rf /Library/Developer/CommandLineTools/SDKs/MacOSX10.14.sdk
conda install -c conda-forge watchdog
pip install streamlit
```

After installing Streamlit, `streamlit run` commands fail with this output:
```
AttributeError: module 'google.protobuf.descriptor' has no attribute '_internal_create_key'
```
This can be fixed by re-installing protobuf:
```bash
pip install python3-protobuf
```

## Run tests locally

```bash
bash scripts/test.sh
```

OR:

```bash
python -m pytest -s
```
