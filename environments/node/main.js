import {readFile} from "node:fs/promises"

(async function(){
    const file = await readFile("output.wasm")
    //const bytes = await file.arrayBuffer()
    const module = new WebAssembly.Module(file)
    const instance = new WebAssembly.Instance(module, {
        env: {
            puti(arg){
                console.log(arg)
            },
            putf(arg){
                console.log(arg)
            },
            puts(offset){
                const [start, length] = new Uint32Array(instance.exports.memory.buffer, offset, 2);
                const bytes = new Uint8Array(instance.exports.memory.buffer, start, length);
                const string = new TextDecoder("utf8").decode(bytes);
                console.log(string);
            }
        }
    })
    instance.exports.main()
})();