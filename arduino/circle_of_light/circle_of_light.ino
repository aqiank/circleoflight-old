#include "LPD8806.h"
#include <SPI.h>
#include <HerkuleX.h>

#define DIMMER 0
#define BAUD_RATE 115200
#define MOTORID 253
#define NUM_LEDS 64
#define LINE_LENGTH (NUM_LEDS * 3)

#define LINE 1
#define FLUSH 2
#define SETTINGS 3
#define RETURN 4
#define END 5

LPD8806 strip(NUM_LEDS);
char line[NUM_LEDS * 3];
int pos = 0;
int line_idx = 0;
int num_lines;
int motor_begin;
int motor_end;

int read16()
{
        while (Serial.available() < 2)
                ;
        return (Serial.read() << 8) | (Serial.read());
}

void read_settings()
{
        num_lines = read16();
        motor_begin = read16();
        motor_end = read16();
}

void setup() {
        strip.begin();
        strip.show();

        Serial.begin(BAUD_RATE);
        HerkuleX.beginSerial1(BAUD_RATE);
        HerkuleX.torqueOn(MOTORID);
}

void loop() {
        int b;

        if (Serial.available()) {
                b = Serial.read();
                switch (b) {
                case LINE:
                        line_idx += 3;
                        pos = ((float) line_idx) / num_lines * abs(motor_end - motor_begin) + motor_begin;
                        Serial.println(pos);
                        HerkuleX.movePos(MOTORID, pos, 1, HERKULEX_LED_GREEN);
                        for (int i = 0; i < LINE_LENGTH; i++) {
                                while (!Serial.available())
                                        ;
                                int r = Serial.read();
                                line[i] = (char) r;
                        }
                        break;
                case FLUSH:
                        flush_line();
                        break;
                case RETURN:
                        clear_line();
                        read_settings();
                        HerkuleX.movePos(MOTORID, motor_begin, 255, HERKULEX_LED_RED);
                        line_idx = 0;
                        pos = 0;
                        break;
                case END:
                        clear_line();
                        break;
                }
        }
}

void flush_line() {
        int r, g, b;

        for (int i = 0; i < LINE_LENGTH / 3; i++) {
                r = line[3 * i] & 0xFF;
                g = line[3 * i + 1] & 0xFF;
                b = line[3 * i + 2] & 0xFF;
                strip.setPixelColor(NUM_LEDS - 1 - i, strip.Color(r >> DIMMER, g >> DIMMER, b >> DIMMER));
        }
        strip.show();
}

void clear_line() {
        int i;

        for (i = 0; i < LINE_LENGTH / 3; i++)
                strip.setPixelColor(i, strip.Color(0, 0, 0));
        strip.show();
}
