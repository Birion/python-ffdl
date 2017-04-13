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
        ("Story", story.title),
        ("Author", story.author),
        ("URL", story.main_url, True),
        ("Author URL", story.author_url, True),
        ("Language", story.language),
        ("Rating", story.rating),
        ("Category", story.category),
        ("Genre", genres),
        ("Characters", characters),
        ("Published", story.published.isoformat()),
        ("Updated", story.updated.isoformat()),
        ("Downloaded", datetime.now()),
        ("Words", story.words),
        ("Chapters", chapters)
    ]
%>
<%def name="is_url(data, url)">
    % if url:
        <a href="${data}">${data}</a>
        %else:
        ${data}
    % endif
</%def>
<%def name="print_metadata(datatype, data, url=False)">
    % if data:
        <div><strong>${datatype}:</strong> ${is_url(data, url)}</div>
    % endif
</%def>
<div class="header">
    <h1>${story.title}</h1> by <h2>${story.author}</h2>
</div>
<div class="titlepage">
    % for data in metadata:
        ${print_metadata(*data)}
    % endfor

    <div><strong>Summary:</strong><p>${story.summary}</p></div>
</div>