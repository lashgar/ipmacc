from xml.dom.minidom import parseString

doc = parseString("""<html>
        <head>
        <script type="text/javascript">
        var a = 'I love &amp;aacute; letters'
        </script>
        </head>
        <body>
        <h1>And I like the fact that 3 &gt; 1</h1>
        </body>
        </html>""")

with open("foo.xhtml", "w") as f:
    f.write( doc.toxml() )

