import ssl
import re
import nltk
from nltk import CFG, ChartParser, Tree
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QComboBox, QTextEdit, QMessageBox
import sys

#creado para evitar errores con ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')

#gramatica
gramatica = CFG.fromstring("""
    E -> E '+' T | E '-' T | T
    T -> T '*' F | T '/' F | F
    F -> '(' E ')' | 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' | 'n' | 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z' | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
""")

#inicializar el parser
parser = ChartParser(gramatica)


#creacion de la interfaz de usuario
class GrammarApp(QMainWindow):
    def __init__(self):
        super().__init__()

        #Dimensiones y el titulo
        self.setWindowTitle('Analizador de Gramáticas')
        self.setGeometry(100, 100, 600, 400)

        #elementos de la interfaz
        layout = QVBoxLayout()
        self.inputLabel = QLabel("Ingresa una expresión:")
        self.inputText = QLineEdit()

        #derecha o izquierda
        self.derivationDirectionLabel = QLabel("Selecciona el tipo de derivación:")
        self.derivationDirection = QComboBox()
        self.derivationDirection.addItems(["Izquierda", "Derecha"])

        self.derivationButton = QPushButton("Generar Derivación")
        self.treeButton = QPushButton("Generar Árbol de Derivación")
        self.astButton = QPushButton("Generar AST")
        self.resultOutput = QTextEdit()
        self.resultOutput.setReadOnly(True)

        # Agrega los elementos al layout
        layout.addWidget(self.inputLabel)
        layout.addWidget(self.inputText)
        layout.addWidget(self.derivationDirectionLabel)
        layout.addWidget(self.derivationDirection)
        layout.addWidget(self.derivationButton)
        layout.addWidget(self.treeButton)
        layout.addWidget(self.astButton)
        layout.addWidget(self.resultOutput)

        #conexion de los botones
        self.derivationButton.clicked.connect(self.generate_derivation)
        self.treeButton.clicked.connect(self.generate_tree)
        self.astButton.clicked.connect(self.generate_ast)

        #organizacion de la interfaz
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    #tokeniza
    def tokenize_expression(self, expression):
        return re.findall(r'\d+|[a-zA-Z]+|[()+\-*/]', expression) #divide una expresion en tokens

    def generate_derivation(self): #genera una derivacion paso a paso
        try:
            expression = self.inputText.text()
            tokens = self.tokenize_expression(expression)
            mode = self.derivationDirection.currentText().lower()
            parse_tree = None

            for tree in parser.parse(tokens):
                parse_tree = tree
                break

            if parse_tree:
                derivation_steps = []
                self.extract_derivation_steps(parse_tree, derivation_steps, mode)

                derivation_text = "\n".join(derivation_steps)
                self.resultOutput.setText(derivation_text)
            else:
                self.resultOutput.setText(f"No se pudo derivar la expresión por {mode}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en derivación: {e}")

    #consulta los pasos para derivacion
    def extract_derivation_steps(self, tree, derivation_steps, mode):
        current_step = "E"
        derivation_steps.append(f"⇒ {current_step}")

        def derivar(subtree):
            nonlocal current_step
            if isinstance(subtree, Tree):
                #construye el arbol
                children_labels = []
                for child in subtree:
                    if isinstance(child, Tree):
                        children_labels.append(child.label())
                    else:
                        children_labels.append(child)

                #actualizacion del paso
                if subtree.label() in current_step:
                    if mode == "izquierda":
                        #izquierda
                        current_step = current_step.replace(subtree.label(), " ".join(children_labels), 1)
                    else:
                        #derecha
                        current_step = current_step[::-1].replace(subtree.label()[::-1], " ".join(children_labels[::-1]), 1)[::-1]
                    derivation_steps.append(f"⇒ {current_step}")

                #derivar el siguiente paso
                for child in (subtree if mode == "izquierda" else reversed(subtree)):
                    derivar(child)

        derivar(tree)


    def generate_tree(self):
        try:
            expression = self.inputText.text()
            tokens = self.tokenize_expression(expression)
            parse_tree = None

            for tree in parser.parse(tokens):
                parse_tree = tree
                break

            if parse_tree:
                parse_tree.draw()  #muestra el arbol
            else:
                QMessageBox.warning(self, "Error", "No se pudo generar el árbol de derivación.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al generar el árbol: {e}")

    #genera el ast
    def generate_ast(self):
        try:
            expression = self.inputText.text()
            tokens = self.tokenize_expression(expression)
            parse_tree = None

            for tree in parser.parse(tokens):
                parse_tree = tree
                break

            if parse_tree:
                ast_tree = self.create_abstract_syntax_tree(parse_tree)
                ast_tree.draw()  #muestra el arbol ast
            else:
                QMessageBox.warning(self, "Error", "No se pudo generar el AST.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al generar el AST: {e}")

    #convieerte el arbol
    def create_abstract_syntax_tree(self, tree):
        def simplificar_arbol(subtree):
            if isinstance(subtree, Tree):
                if subtree.label() in {'E', 'T', 'F'}:
                    #reemplaza siguiendo la gramatica
                    if len(subtree) == 1:
                        return simplificar_arbol(subtree[0])
                    elif subtree.label() == 'F' and len(subtree) == 3:
                        #no parentesis
                        return simplificar_arbol(subtree[1])
                    else:
                        return [simplificar_arbol(child) for child in subtree]
                else:
                    return [simplificar_arbol(child) for child in subtree]
            else:
                return subtree

        simplified_tree = simplificar_arbol(tree)

        def reconstruir_arbol(nodos):
            if isinstance(nodos, list):
                if len(nodos) == 1:
                    return reconstruir_arbol(nodos[0])
                else:
                    if len(nodos) == 3 and isinstance(nodos[1], str):
                        return Tree(nodos[1], [reconstruir_arbol(nodos[0]), reconstruir_arbol(nodos[2])])
                    else:
                        return [reconstruir_arbol(nodo) for nodo in nodos]
            else:
                return nodos

        return reconstruir_arbol(simplified_tree)


#corre el codigo
def main():
    app = QApplication(sys.argv)
    window = GrammarApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
