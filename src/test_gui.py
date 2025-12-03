import dearpygui.dearpygui as dpg

# Setup
dpg.create_context()
dpg.create_viewport(title='Test', width=400, height=300)

# Create a window
with dpg.window(label="Hello Centaur!"):
    dpg.add_text("Congratulations! 🎉")
    dpg.add_text("Dear PyGui is working!")
    dpg.add_button(label="Click me", callback=lambda: print("Button clicked"))
    dpg.add_slider_float(label="Slider", default_value=0.5, max_value=1.0)

# Show and run
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
