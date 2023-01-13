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
                //we have to put in a uint8 array because the uint32 may be stored at a non
                //multiple of 4 index.
                const fields = new Uint8Array(instance.exports.memory.buffer, offset, 8);
                const start = fields.slice(0, 4)[0]
                const length = fields.slice(4, 8)[0]
                const bytes = new Uint8Array(instance.exports.memory.buffer, start, length);
                const string = new TextDecoder("utf8").decode(bytes);
                console.log(string);
            }
        }
    })
    instance.exports.main()
})();