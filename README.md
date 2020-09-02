# fantasy-football


# Developer Set up

```
pip install --upgrade -r requirements.txt
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
