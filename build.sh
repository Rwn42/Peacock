python3 src/main.py com examples/test.pk > output.wat
~/tools/wabt-1.0.32/bin/wat2wasm output.wat
mv output.wasm environments/web/output.wasm
#rm output.wat