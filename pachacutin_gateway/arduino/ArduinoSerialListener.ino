// ArduinoSerialListener.ino
// Ejemplo mínimo: escucha líneas por USB serial y actúa según el comando
void setup() {
  Serial.begin(115200);
  // inicializar pines/servos aquí
  pinMode(13, OUTPUT);
  Serial.println("Arduino ready");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    if (line.length() > 0) {
      char cmd = line.charAt(0);
      Serial.print("Recibido: "); Serial.println(cmd);
      switch (cmd) {
        case 'A': // ejemplo: encender LED
          digitalWrite(13, HIGH);
          break;
        case 'B': // apagar LED
          digitalWrite(13, LOW);
          break;
        case 'S': // sembrar (placeholder)
          // implementa tu lógica de servos
          break;
        default:
          // no reconocido
          break;
      }
    }
  }
}
