## coding=utf-8
<%
    number_of_chapters = len(story.chapters) if story.complete else "??"
    chapters = "{}/{}".format(len(story.chapters), number_of_chapters)
    genres = "/".join(story.genres) if story.genres else None
    tags = ", ".join(story.tags) if story.tags else None
    characters = None
    if story.characters:
        characters = ""
        if story.characters["couples"]:
            couples = ["[" + ", ".join(x) + "]" for x in story.characters["couples"]]
            characters += " ".join(couples)
            if story.characters["singles"]:
                characters += " "
        if story.characters["singles"]:
            characters += ", ".join(story.characters["singles"])

    metadata = [
        ("Story", story.title, "title"),
        ("Author", story.author.name, "author"),
        ("URL", story.url, "story-url", True),
        ("Author URL", story.author.url, "author-url", True),
        ("Language", story.language, "lang"),
        ("Rating", story.rating, "rating"),
        ("Category", story.category, "category"),
        ("Genre", genres, "genres"),
        ("Characters", characters, "characters"),
        ("Published", story.published.to_iso8601_string() if story.published else None, "published"),
        ("Updated", story.updated.to_iso8601_string() if story.updated else None, "updated"),
        ("Downloaded", story.downloaded.to_iso8601_string(), "downloaded"),
        ("Words", story.words, "words"),
        ("Tags", tags, "tags"),
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
    <h1>${story.title}</h1> by <h2>${story.author.name}</h2>
</div>
<div class="titlepage">
    % for data in metadata:
        % if data[1]:
            ${print_metadata(*data)}
        % endif
    % endfor
    % if story.summary:
        <div>
            <strong>Summary:</strong>
            <p>${story.summary}</p>
        </div>
    % endif
</div>
