service ProxyPool{
    void spot_proxy(1:string ip, 2:i32 port, 3:string country),
    bool has_proxy(1:string proxy_url),
    string req_proxy(1:string url),
    void free_proxy(1:string proxy_url, 2:double latency)
}