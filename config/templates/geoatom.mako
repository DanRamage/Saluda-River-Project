<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:georss="http://www.georss.org/georss">
    <title>${title}</title>
    <subtitle>${subtitle}</subtitle>
    <link href='${site_url}'/>
    <updated>${update_datetime}</updated>
    <author>
        <name>${author}</name>
        <email>${author_email}</email>
    </author>
    <id>${main_id}</id>
    % for georss_rec in georss_recs:
        <entry>
            <title>${georss_rec.title}</title>
            <link href='${georss_rec.link}'/>
            <id>${georss_rec.id}</id>
            <updated>${georss_rec.update_datetime}</updated>
            <summary>${georss_rec.summary}</summary>
            <georss:point>${georss_rec.longitude} ${georss_rec.latitude}</georss:point>
        </entry>
    % endfor
</feed>
