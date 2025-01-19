from typing import TypedDict, Optional

import panel as pn
import param
from panel.custom import ReactComponent
from panel.models.esm import DataEvent
from param import List

pn.extension()

# --------------------------------------------------
# 1) Define a TypedDict for the shortcut structure
# --------------------------------------------------
class KeyboardShortcut(TypedDict):
    name: str
    key: str
    altKey: Optional[bool]
    ctrlKey: Optional[bool]
    metaKey: Optional[bool]
    shiftKey: Optional[bool]


# --------------------------------------------------
# 2) Define the KeyboardShortcuts React component
# --------------------------------------------------
class KeyboardShortcuts(ReactComponent):
    """
    Installs global keyboard shortcuts into a Panel app.

    Pass in a list of KeyboardShortcut dictionaries, and handle them
    using .on_msg(callback). The callback receives a DataEvent whose
    .data is the 'name' field from the triggered shortcut.
    """

    shortcuts = List(class_=dict)

    # The _esm code is embedded JavaScript/React to capture keydown events
    # and send a message back to Python whenever a shortcut is matched.
    _esm = """
    // Hash a shortcut to a consistent string
    function hashShortcut({ key, altKey, ctrlKey, metaKey, shiftKey }) {
      return `${key}.${+!!altKey}.${+!!ctrlKey}.${+!!metaKey}.${+!!shiftKey}`;
    }

    export function render({ model }) {
      const [shortcuts] = model.useState("shortcuts");

      const keyedShortcuts = {};
      for (const shortcut of shortcuts) {
        keyedShortcuts[hashShortcut(shortcut)] = shortcut.name;
      }

      function onKeyDown(e) {
        const name = keyedShortcuts[hashShortcut(e)];
        if (name) {
          e.preventDefault();
          e.stopPropagation();
          model.send_msg(name);
        }
      }

      React.useEffect(() => {
        window.addEventListener('keydown', onKeyDown);
        return () => {
          window.removeEventListener('keydown', onKeyDown);
        };
      }, []);

      return <></>;
    }
    """


# --------------------------------------------------
# 3) Demo: define shortcuts and show usage
# --------------------------------------------------
# Create two global shortcuts: Ctrl+S => "save", Ctrl+P => "print"
shortcuts = [
    KeyboardShortcut(name="save",  key="s", ctrlKey=True),
    KeyboardShortcut(name="print", key="p", ctrlKey=True),
]

# Instantiate the KeyboardShortcuts component
shortcut_component = KeyboardShortcuts(shortcuts=shortcuts)

# A simple text widget to display what's triggered
message = pn.widgets.StaticText(value="Press Ctrl+S or Ctrl+P...")

# Handle the incoming message event
def handle_shortcut(event: DataEvent):
    """
    event.data will be the name of the matching shortcut.
    """
    if event.data == "save":
        message.value = "Save shortcut triggered!"
    elif event.data == "print":
        message.value = "Print shortcut triggered!"

# Subscribe to keyboard shortcut events
shortcut_component.on_msg(handle_shortcut)

# # --------------------------------------------------
# # 4) Serve everything in a layout
# # --------------------------------------------------
# layout = pn.Column(
#     "# KeyboardShortcuts Demo",
#     message,
#     "Try pressing Ctrl+S or Ctrl+P in this window.",
#     shortcut_component
# )
#
# pn.serve(layout)
