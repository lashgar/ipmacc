from lxml.builder import E
from lxml import etree

def CLASS(*args):
    return {"class":' '.join(args)}

html = page = (
        E.html(
            E.head(
                E.title("This is a sample document")
                ),
            E.body(
                E.h1("Hello!", CLASS("title")),
                E.p("This is a paragraph with ", E.b("bold"), " text in it!"),
                E.p("This is another paragraph, with a", "\n      ",
                    E.a("link", href="http://www.python.org"), "."),
                E.p("Here are some reservered characters: <spam&egg>."),
                )
            )
        )

print(etree.tostring(page, pretty_print=True))
