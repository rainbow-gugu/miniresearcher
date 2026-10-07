### 编程语言多维度对比表

| 维度 | Python | Java | Go | Rust | JavaScript |
| --- | --- | --- | --- | --- | --- |
| 类型系统 | 动态强类型，可选类型注解（mypy） | 静态强类型，泛型，编译期检查 | 静态强类型，接口隐式实现，1.18+ 支持泛型 | 静态强类型，所有权/借用检查，trait 系统 | 动态弱类型，TypeScript 提供静态类型 |
| 并发模型 | GIL 限制多线程；asyncio 协程；multiprocessing 多进程 | 原生多线程 + JUC 并发包；虚拟线程（JDK21） | goroutine + channel（CSP 模型），轻量级 | 无数据竞争的并发（Send/Sync），async/await | 单线程事件循环 + 异步回调/Promise/async-await |
| 运行环境 | CPython 解释器（字节码），跨平台 | JVM（字节码 + JIT 编译），跨平台 | 编译为原生机器码，静态链接，单二进制 | 编译为原生机器码，无 GC，可嵌入 | 浏览器 / Node.js（V8 引擎） |
| 包管理 | pip / conda / uv，PyPI 生态 | Maven / Gradle，Maven Central | go modules，标准库丰富 | Cargo + crates.io | npm / yarn / pnpm，npm 生态最大 |
| 性能 | 解释执行，较慢；可用 C 扩展 / NumPy / Cython 加速 | JIT 优化后接近原生，启动较慢、内存占用高 | 接近 C/C++，编译快，GC 停顿低 | 与 C/C++ 相当，零成本抽象，内存安全 | JIT 优化，中等；Node 适合 I/O 密集 |
| 典型用途 | 数据科学、AI/ML、脚本、Web 后端、自动化 | 企业级后端、Android、大数据（Hadoop/Spark） | 云原生、微服务、网络服务、CLI 工具、DevOps | 系统编程、嵌入式、高性能服务、WASM、区块链 | 前端 Web、全栈、Node 后端、脚本 |
| 学习曲线 | 平缓，语法简洁，入门友好 | 中等，样板代码多，生态庞大 | 平缓，语言特性少，易上手 | 陡峭，所有权与生命周期概念较难 | 平缓入门，异步与类型陷阱需注意 |
