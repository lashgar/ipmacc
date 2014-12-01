from xml.etree.ElementTree.SimpleXMLWriter import XMLWriter
import sys

w = XMLWriter(sys.stdout)
html = w.start("html")

w.start("head")
w.element("title", "my document")
w.element("meta", name="generator", value="my application 1.0")
w.end()

w.start("body")
w.element("h1", "this is a heading")
w.element("p", "this is a paragraph")

w.start("p")
w.data("this is ")
w.element("b", "bold")
w.data(" and ")
w.element("i", "italic")
w.data(".")
w.end("p")

w.close(html)
