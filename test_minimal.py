import gradio as gr
print("Starting minimal test...")
demo = gr.Interface(lambda x: f"Hello {x}", "text", "text")
print("Launching...")
demo.launch(server_port=7860)
print("Done!")