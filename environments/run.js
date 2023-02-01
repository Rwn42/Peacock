const customEnvironment = {
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
    },
    alloc(n, size){
        const result = instance.exports.mem_head.value;
        instance.exports.mem_head.value += (n*size);
        return result;
    },
    read(location){
        const result = new Uint8Array(instance.exports.memory.buffer, location, 4);
        return result[0];
    },
    write(location, value){
        const buffer = new Uint8Array(instance.exports.memory.buffer, location);
        buffer[0] = value;
    },

    async startServer(homePagePointer){
        const fields = new Uint8Array(instance.exports.memory.buffer, homePagePointer, 8);
        const start = fields.slice(0, 4)[0]
        const length = fields.slice(4, 8)[0]
        const bytes = new Uint8Array(instance.exports.memory.buffer, start, length);
        const payload = new TextDecoder("utf8").decode(bytes);
        async function handleHttp(conn) {
            for await (const e of Deno.serveHttp(conn)) {
              console.log(e.request.url)
              if(e.request.url.endsWith("/")){
                e.respondWith(new Response(new TextEncoder().encode(payload)));
              }
              
            }
          }
          
        for await (const conn of Deno.listen({ port: 8080 })) {
            handleHttp(conn);
        }
    }
}

const wasmFile = await Deno.readFile("./environments/output.wasm");
const module = new WebAssembly.Module(wasmFile)
const instance = new WebAssembly.Instance(module, {
    env: customEnvironment
});
instance.exports.main()
