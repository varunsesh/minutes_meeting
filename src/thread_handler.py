import threading

class ThreadHandler:
    def __init__(self):
        self.threads = []
        self.stop_events = []

    def start_new_thread(self, target, args=()):
        """Starts a new thread for a given target function and arguments."""
        stop_event = threading.Event()
        thread = threading.Thread(target=self.thread_target, args=(target, args, stop_event))
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
        self.stop_events.append(stop_event)

    def thread_target(self, target, args, stop_event):
        """Wrapper for the target function to incorporate stop event."""
        target(*args, stop_event)

    def stop_threads(self):
        """Sets the event to signal all threads to stop."""
        for event in self.stop_events:
            event.set()
        for thread in self.threads:
            thread.join()

    def stop_thread(self, thread_index):
        """Stops a specific thread based on its index."""
        if thread_index < len(self.threads):
            self.stop_events[thread_index].set()
            self.threads[thread_index].join()