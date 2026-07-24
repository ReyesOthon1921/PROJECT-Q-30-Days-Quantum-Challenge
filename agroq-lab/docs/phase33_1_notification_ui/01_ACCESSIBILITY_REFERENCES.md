# Accessibility and Interaction References

The refinement follows these official patterns:

- W3C WAI-ARIA Authoring Practices switch pattern
- W3C switch example using a native HTML checkbox input
- W3C guidance for fieldset and legend grouping
- W3C focus-visible techniques
- MDN guidance to use explicit labels and native checkbox controls

The implementation keeps a native checkbox as the real form control and uses CSS only
for the visual switch. The visible label never changes. On/Off text supplements the
graphical state. Spacebar behavior, focus, and form submission remain native.
