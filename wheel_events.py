# wheel_events.py
import param
from panel.custom import ReactComponent

class WheelEvents(ReactComponent):
    """
    A Panel/React component that listens globally for mouse wheel events
    and *always* blocks the default scroll/zoom behavior. The .on_msg()
    callback in Python gets "up" or "down" depending on the scroll direction.
    """

    intercept = param.Boolean(default=True)

    _esm = """
    export function render({ model }) {
      const [ intercept ] = model.useState("intercept");

      function onWheel(e) {
        // If we're intercepting, block the event from anywhere in the DOM:
        if (intercept) {
          e.stopImmediatePropagation();
          e.stopPropagation();
          e.preventDefault();
        }
        // e.deltaY < 0 => scrolled up, > 0 => scrolled down
        const direction = e.deltaY < 0 ? "up" : "down";
        model.send_msg(direction);
      }

      React.useEffect(() => {
        // capture=true => run this handler before Bokeh/HoloViews
        // passive=false => we can call preventDefault()
        const opts = { passive: false, capture: true };
        window.addEventListener('wheel', onWheel, opts);
        return () => {
          window.removeEventListener('wheel', onWheel, opts);
        };
      }, [intercept]);

      return <></>;
    }
    """
