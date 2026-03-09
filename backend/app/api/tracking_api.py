"""Tracking API — serves the landing page JS tracking snippet."""

import logging

from fastapi import APIRouter, Query
from fastapi.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter()

# Minimal tracking snippet — reads UTMs, tracks scroll + time, POSTs on unload.
# Configured per account via account_slug and api_base query params.
_SNIPPET_TEMPLATE = r"""
(function(cfg){
  var slug=cfg.slug||'',base=cfg.base||'',p={},st=Date.now(),sd=0;
  // Parse UTMs
  var q=location.search.slice(1).split('&');
  for(var i=0;i<q.length;i++){
    var kv=q[i].split('=');
    if(kv[0]&&kv[1])p[decodeURIComponent(kv[0])]=decodeURIComponent(kv[1]);
  }
  // Track scroll depth
  function onScroll(){
    var h=document.documentElement,b=document.body;
    var t=Math.max(h.scrollTop,b.scrollTop);
    var full=Math.max(h.scrollHeight,b.scrollHeight)-h.clientHeight;
    var pct=full>0?Math.round(t/full*100):0;
    if(pct>sd)sd=pct;
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  // Send on unload
  function send(){
    var payload={
      account_slug:slug,
      page_url:location.href,
      utm_campaign:p.utm_campaign||null,
      utm_source:p.utm_source||null,
      utm_medium:p.utm_medium||null,
      utm_content:p.utm_content||null,
      utm_term:p.utm_term||null,
      scroll_depth_percent:sd,
      time_on_page_seconds:Math.round((Date.now()-st)/1000),
      device_type:navigator.maxTouchPoints>0?'mobile':'desktop',
      browser:navigator.userAgent.substring(0,100)
    };
    var url=(base||'')+'/api/webhooks/landing-page';
    if(navigator.sendBeacon){
      navigator.sendBeacon(url,JSON.stringify(payload));
    } else {
      var xhr=new XMLHttpRequest();
      xhr.open('POST',url,false);
      xhr.setRequestHeader('Content-Type','application/json');
      try{xhr.send(JSON.stringify(payload));}catch(e){}
    }
  }
  window.addEventListener('beforeunload',send);
  // Milestone scroll tracking
  [25,50,75,100].forEach(function(m){
    var fired=false;
    window.addEventListener('scroll',function(){
      if(!fired&&sd>=m){fired=true;}
    },{passive:true});
  });
})(window.__ATLAS_CFG__||{slug:'ACCOUNT_SLUG',base:'API_BASE'});
""".strip()


@router.get("/snippet.js", response_class=Response)
async def tracking_snippet(
    account_slug: str = Query(..., description="Account slug to embed in the snippet"),
    api_base: str = Query("", description="Base URL of the ATLAS API (e.g. https://api.example.com)"),
):
    """
    Serve the ATLAS landing page tracking JavaScript snippet.
    Embed on landing pages by adding:
      <script>window.__ATLAS_CFG__={slug:'your-slug',base:'https://api.yoursite.com'};</script>
      <script src="/api/tracking/snippet.js?account_slug=your-slug&api_base=..."></script>
    """
    logger.debug("Serving tracking snippet for slug=%s", account_slug)

    # Inject config directly into the snippet for the requested account
    snippet = _SNIPPET_TEMPLATE.replace("ACCOUNT_SLUG", account_slug).replace(
        "API_BASE", api_base
    )

    return Response(
        content=snippet,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Account-Slug": account_slug,
        },
    )
