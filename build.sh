deno run --allow-all  ./src/main.ts ./testing/test.pk -c -o ./output
~/tools/wabt-1.0.32/bin/wat2wasm output.wat
rm output.wat
mv output.wasm ./environments/output.wasm
deno run --allow-all ./environments/run.js