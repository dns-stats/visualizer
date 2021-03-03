function logURL(requestDetails) {
    const body = requestDetails.requestBody;
    if ( body ) {
        if ( body.raw ) {
            let dec = new TextDecoder("utf-8");
            for ( let i = 0; i < body.raw.length; i++ ) {
                let s = body.raw[i].bytes;
                console.log("\n%s\n", dec.decode(s));
            }
        }
    }
}

chrome.webRequest.onBeforeRequest.addListener(
    logURL,
    {urls: ["*://*/api*","*://*/stats/api*"]},
    ["requestBody"]
);
