<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
     xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel>
        <title>${title}</title>
        <link href='${site_url}'/>
        <description>${subtitle}</description>
        <dc:publisher>${author}</dc:publisher>
        <pubDate>${update_datetime}</pubDate>
        % for georss_rec in georss_recs:
            <item>
                <title>${georss_rec.title}</title>
                <link href='${georss_rec.link}'/>
                <guid isPermaLink="true">${georss_rec.id}</guid>
                <pubDate>${georss_rec.update_datetime}</pubDate>
                <description>${georss_rec.summary}</description>
                <geo:long>${georss_rec.longitude}</geo:long>
                <geo:lat>${georss_rec.latitude}</geo:lat>
            </item>
        % endfor
    </channel>
</rss>