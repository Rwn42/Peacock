let instance;


async function load(){
    const file = await fetch("./output.wasm");
    const bytes = await file.arrayBuffer()
    const module = new WebAssembly.Module(bytes)
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
    console.log(instance.exports.memory)

};

function get_instance() {return instance}

load()