## coding=utf-8
<%!
    from datetime import datetime
%>
<%
    number_of_chapters = len(story.chapters) if story.complete else "??"
    chapters = "{}/{}".format(len(story.chapters), number_of_chapters)
    genres = "/".join(story.genres) if story.genres else None
    characters = ", ".join(story.characters) if story.characters else None

    metadata = [
        ("Story", story.title, "title"),
        ("Author", story.author["name"], "author"),
        ("URL", story.main_url, "story-url", True),
        ("Author URL", story.author["url"], "author-url", True),
        ("Language", story.language, "lang"),
        ("Rating", story.rating, "rating"),
        ("Category", story.category, "category"),
        ("Genre", genres, "genres"),
        ("Characters", characters, "characters"),
        ("Published", story.published.isoformat(), "published"),
        ("Updated", story.updated.isoformat(), "updated"),
        ("Downloaded", datetime.now(), "downloaded"),
        ("Words", story.words, "words"),
        ("Chapters", chapters, "chapters")
    ]
%>
<%def name="is_url(data, url)">
    % if url:
        <a href="${data}">${data}</a>
        %else:
        ${data}
    % endif
</%def>
<%def name="print_metadata(datatype, data, id, url=False)">
    % if data:
        <div id="${id}"><strong>${datatype}:</strong> ${is_url(data, url)}</div>
    % endif
</%def>
<div class="header">
    <h1>${story.title}</h1> by <h2>${story.author["name"]}</h2>
</div>
<div class="titlepage">
    % for data in metadata:
        ${print_metadata(*data)}
    % endfor

    <div><strong>Summary:</strong><p>${story.summary}</p></div>
</div>