"""
Centaur Parting - SIMPLE Dashboard
Absolute simplest version to debug display issues
"""

import dearpygui.dearpygui as dpg

class SimpleDashboard:
    def __init__(self):
        self.width = 1200
        self.height = 700
        
    def create_window(self):
        """Create simplest possible window"""
        with dpg.window(label="Centaur Parting", width=self.width, height=self.height):
            
            # Title
            dpg.add_text("CENTAUR PARTING - ASTROPHOTOGRAPHY MONITOR", 
                        color=(100, 150, 255))
            dpg.add_separator()
            
            # SIMPLE table layout
            with dpg.table(header_row=False, borders_innerH=True, 
                          borders_outerH=True, borders_innerV=True, 
                          borders_outerV=True, row_background=True):
                
                dpg.add_table_column(width=600)  # Left column
                dpg.add_table_column(width=600)  # Right column
                
                # ROW 1: Headers
                with dpg.table_row():
                    dpg.add_text("ACTIVE RIGS")
                    dpg.add_text("ALERTS & STATS")
                
                # ROW 2: Content
                with dpg.table_row():
                    # LEFT: Rig info
                    with dpg.child_window(height=300):
                        dpg.add_text("RIG 1: M81")
                        dpg.add_text("Filter: Luminance")
                        dpg.add_text("HFR: 2.8 pixels")
                        dpg.add_text("SNR: 14.2")
                        dpg.add_text("Exposure: 300s")
                        dpg.add_progress_bar(default_value=0.375, width=300)
                        dpg.add_text("45 of 120 frames")
                        
                        dpg.add_spacer(height=20)
                        
                        dpg.add_text("RIG 2: NGC7000")
                        dpg.add_text("Filter: Hydrogen-Alpha")
                        dpg.add_text("HFR: 3.5 pixels")
                        dpg.add_text("SNR: 8.7")
                        dpg.add_text("Exposure: 600s")
                        dpg.add_progress_bar(default_value=0.22, width=300)
                        dpg.add_text("22 of 100 frames")
                    
                    # RIGHT: Alerts
                    with dpg.child_window(height=300):
                        dpg.add_text("SYSTEM STATUS", color=(255, 150, 100))
                        dpg.add_separator()
                        
                        dpg.add_text("[OK] Guiding stable")
                        dpg.add_text("[WARNING] Focus drift detected")
                        dpg.add_text("[INFO] Clouds detected")
                        dpg.add_text("[OK] SNR target reached")
                        
                        dpg.add_spacer(height=20)
                        
                        dpg.add_text("SUGGESTIONS", color=(100, 200, 255))
                        dpg.add_separator()
                        
                        dpg.add_text("1. Increase Ha exposure to 600s")
                        dpg.add_text("2. Refocus Rig 2")
                        dpg.add_text("3. Check for clouds")
                
                # ROW 3: Bottom stats
                with dpg.table_row():
                    with dpg.child_window(height=100):
                        dpg.add_text("TOTAL STATISTICS")
                        dpg.add_separator()
                        dpg.add_text("Frames captured: 1,247")
                        dpg.add_text("Total integration: 62.3 hours")
                        dpg.add_text("Success rate: 94.2%")
                    
                    with dpg.child_window(height=100):
                        dpg.add_button(label="REFRESH DATA", width=200, height=40)
                        dpg.add_spacer()
                        dpg.add_text("Last update: Just now")
    
    def run(self):
        """Run the simple dashboard"""
        dpg.create_context()
        dpg.create_viewport(title='Centaur Parting', 
                           width=self.width, height=self.height)
        
        # Simple dark theme
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 230, 240, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 80, 120, 255))
        
        self.create_window()
        dpg.bind_theme(theme)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    print("Starting simple dashboard...")
    dashboard = SimpleDashboard()
    dashboard.run()
