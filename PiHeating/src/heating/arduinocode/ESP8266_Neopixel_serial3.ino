// NeoPixelFunFadeInOut
// This example will randomly pick a color and fade all pixels to that color, then
// it will fade them to black and restart over
//
// This example demonstrates the use of a single animation channel to animate all
// the pixels at once.
//
#include <NeoPixelBus.h>
#include <NeoPixelAnimator.h>

const uint16_t PixelCount = 12; // make sure to set this to the number of pixels in your strip
const uint8_t PixelPin = 2;  // D4 make sure to set this to the correct pin, ignored for Esp8266
const uint8_t AnimationChannels = 15; // we only need one as all the pixels are animated at once
char heartPixels[8] = {1, 2, 4, 5, 7, 8, 10, 11};

const uint8_t BOILER_BUTTON = 5;  // D1
uint8_t boilerBtnState = 1;       

const uint8_t CHECK_BUTTON = 4;   // D2
uint8_t checkBtnState = 1;

const uint8_t OVER_BUTTON = 0;    // D3
uint8_t overBtnState = 1;

const uint8_t REBOOT_BUTTON = 14; // D5
uint8_t rebootBtnState = 1;

const uint8_t SHUTDOWN_BUTTON = 12; // D6
uint8_t shutdownBtnState = 1;

const uint8_t RELAY_OUT = 13; // D7


const uint16_t PixelFadeDuration = 400; // half a second
// one second divide by the number of pixels = loop once a second
const uint16_t NextPixelMoveDuration = 1000 / PixelCount; // how fast we move through the pixels

//NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> strip(PixelCount, PixelPin);
// For Esp8266, the Pin is ignored and it uses GPIO3.
// There are other Esp8266 alternative methods that provide more pin options, but also have
// other side effects.
NeoPixelBus<NeoGrbFeature, NeoEsp8266Uart800KbpsMethod> strip(PixelCount, PixelPin);
// NeoEsp8266Uart800KbpsMethod also ignores the pin parameter and uses GPI02
//NeoPixelBus<NeoGrbFeature, NeoEsp8266BitBang800KbpsMethod> strip(PixelCount, PixelPin);
// NeoEsp8266Uart800KbpsMethod will work with all but pin 16, but is not stable with WiFi
// being active

NeoPixelAnimator animations(AnimationChannels); // NeoPixel animation management object

uint16_t effectState = 0;  // general purpose variable used to store effect state

uint16_t cubeState = 0;
uint16_t currentcubeState = 1;

uint16_t veraState = 0;
uint16_t currentveraState = 1;

uint16_t heatState = 2;
uint16_t currentheatState = 0;
uint16_t heatCycle = 0;
uint16_t heatTime = 0;

uint16_t boilerState = 0;
uint16_t currentboilerState = 1;

uint16_t chaseState = 0;
uint16_t chaseCycle = 0;

uint16_t overrideState = 2;
uint16_t currentoverrideState = 1;
uint16_t forceUpdate = 0;

uint16_t lightArg = 0;

void SetLights();


// what is stored for state is specific to the need, in this case, the colors.
// basically what ever you need inside the animation update function
struct MyAnimationState
{
  RgbColor StartingColor;
  RgbColor EndingColor;
  uint16_t IndexPixel; // which pixel this animation is effecting
};

// one entry per pixel to match the animation timing manager
MyAnimationState animationState[AnimationChannels];

uint16_t frontPixel = 0;  // the front of the loop
uint16_t indexPixel = 0;  // the front of the loop
RgbColor frontColor;  // the color at the front of the loop

// simple blend function
void BlendAnimUpdate(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);

  // apply the color to the strip
  for (uint16_t pixel = 0; pixel < 8; pixel++)
  {
    strip.SetPixelColor(heartPixels[pixel], updatedColor);
  }
}

void BlendSinglePixel(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);

  strip.SetPixelColor(3, updatedColor);
}

void BlendVeraPixel(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);

  strip.SetPixelColor(9, updatedColor);
}

void BlendBoilerPixel(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);

  strip.SetPixelColor(0, updatedColor);
}

void BlendOverridePixel(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);

  strip.SetPixelColor(6, updatedColor);
}


void FadeCube(float luminance)
{
  uint16_t time = 2000;
  if (cubeState == 1) {
    RgbColor target = HslColor(120 / 360.0f, 1.0f, luminance);
    animationState[1].StartingColor = strip.GetPixelColor(3);
    animationState[1].EndingColor = target;

    animations.StartAnimation(1, time, BlendSinglePixel);
    currentcubeState = 1;
  }
  else if (cubeState == 0) {
    RgbColor target = HslColor(30 / 360.0f, 1.0f, luminance);
    animationState[1].StartingColor = strip.GetPixelColor(3);
    animationState[1].EndingColor = target;

    animations.StartAnimation(1, time, BlendSinglePixel);
    currentcubeState = 0;
  }
}

void FadeVera(float luminance)
{
  uint16_t time = 2000;
  if (veraState == 1) {
    RgbColor target = HslColor(120 / 360.0f, 1.0f, luminance);
    animationState[2].StartingColor = strip.GetPixelColor(9);
    animationState[2].EndingColor = target;

    animations.StartAnimation(2, time, BlendVeraPixel);
    currentveraState = 1;
  }
  else if (veraState == 0) {
    RgbColor target = HslColor(30 / 360.0f, 1.0f, luminance);
    animationState[2].StartingColor = strip.GetPixelColor(9);
    animationState[2].EndingColor = target;

    animations.StartAnimation(2, time, BlendVeraPixel);
    currentveraState = 0;
  }
}

void FadeBoiler(float luminance)
{
  uint16_t time = 2000;
  if (boilerState == 1) {
    RgbColor target = HslColor(120 / 360.0f, 1.0f, luminance);
    animationState[3].StartingColor = strip.GetPixelColor(6);
    animationState[3].EndingColor = target;

    animations.StartAnimation(3, time, BlendBoilerPixel);
    currentboilerState = 1;
  }
  else if (boilerState == 0) {
    RgbColor target = HslColor(30 / 360.0f, 1.0f, luminance);
    animationState[3].StartingColor = strip.GetPixelColor(6);
    animationState[3].EndingColor = target;

    animations.StartAnimation(3, time, BlendBoilerPixel);
    currentboilerState = 0;
  }
}

void FadeOverride(float luminance)
{
  uint16_t time = 2000;
  if (overrideState == 1) {
    RgbColor target = HslColor(360 / 360.0f, 1.0f, luminance);
    animationState[5].StartingColor = strip.GetPixelColor(6);
    animationState[5].EndingColor = target;

    animations.StartAnimation(5, time, BlendOverridePixel);
    currentoverrideState = 1;
  }
  else if (overrideState == 0) {
    RgbColor target = HslColor(200 / 360.0f, 1.0f, luminance);
    animationState[5].StartingColor = strip.GetPixelColor(6);
    animationState[5].EndingColor = target;

    animations.StartAnimation(5, time, BlendOverridePixel);
    currentoverrideState = 0;
  }
  else if (overrideState == 2) {
    RgbColor target = HslColor(120 / 360.0f, 1.0f, luminance);
    animationState[5].StartingColor = strip.GetPixelColor(6);
    animationState[5].EndingColor = target;

    animations.StartAnimation(5, time, BlendOverridePixel);
    currentoverrideState = 2;
  }

  //currentoverrideState = 3;
}

void FadeInFadeOutRinseRepeat(float luminance, int color)
{
  uint16_t time = 4000;
  if (effectState == 0)
  {
    // Fade upto a random color
    // we use HslColor object as it allows us to easily pick a hue
    // with the same saturation and luminance so the colors picked
    // will have similiar overall brightness
    RgbColor target = HslColor(color / 360.0f, 1.0f, luminance);
    //uint16_t time = 1000;
    if (heatState == 1) {
      RgbColor target = HslColor(360 / 360.0f, 1.0f, luminance);
    }
    else {
      RgbColor target = HslColor(200 / 360.0f, 1.0f, luminance);
    }
    

    animationState[0].StartingColor = strip.GetPixelColor(1);
    animationState[0].EndingColor = target;


    animations.StartAnimation(0, time, BlendAnimUpdate);
  }
  else if (effectState == 1)
  {
    // fade to black
    //uint16_t time = 1000;

    animationState[0].StartingColor = strip.GetPixelColor(1);
    animationState[0].EndingColor = RgbColor(0);

    animations.StartAnimation(0, time, BlendAnimUpdate);
    heatCycle = (heatCycle + 1);
  }

  // toggle to the next effect state
  effectState = (effectState + 1) % 2;

}

void FadeOutAnimUpdate(const AnimationParam& param)
{
  RgbColor updatedColor = RgbColor::LinearBlend(
                            animationState[param.index].StartingColor,
                            animationState[param.index].EndingColor,
                            param.progress);
  // apply the color to the strip
  strip.SetPixelColor(animationState[param.index].IndexPixel, updatedColor);
}

void LoopAnimUpdate(const AnimationParam& param)
{
  if (param.state == AnimationState_Completed && chaseCycle < 5)
  {
    // done, time to restart this position tracking animation/timer
    animations.RestartAnimation(param.index);

    // pick the next pixel inline to start animating
    //
    //frontPixel = (frontPixel + 1) % PixelCount; // increment and wrap

    //frontPixel = (frontPixel + 1) % PixelCount; // increment and wrap
    indexPixel = (indexPixel + 1) % 8;
    frontPixel = heartPixels[indexPixel];


    
    if (frontPixel == 1)
    {
      // we looped, lets pick a new front color
      chaseCycle = (chaseCycle + 1);
      //Serial.println(chaseCycle);
      frontColor = HslColor(300 / 360.0f, 1.0f, 0.25f);
    }

    uint16_t indexAnim;
    if (animations.NextAvailableAnimation(&indexAnim, 0))
    {
      animationState[indexAnim].StartingColor = frontColor;
      animationState[indexAnim].EndingColor = RgbColor(0, 0, 0);
      animationState[indexAnim].IndexPixel = frontPixel;

      animations.StartAnimation(indexAnim, PixelFadeDuration, FadeOutAnimUpdate);
    }
  }
  else {
    forceUpdate = 1;
    SetLights();
    forceUpdate = 0;
  }
}

void SetLights()
{
  if ((overrideState != currentoverrideState) || forceUpdate == 1) {

    if (animations.IsAnimationActive(5)) {
      exit;
    }
    else {
      FadeOverride(0.2f); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }
  }
  if (chaseState == 1) {
    if (animations.IsAnimationActive(4)) {
      exit;
    }
    else if (chaseCycle < 3) {
      animations.StartAnimation(4, NextPixelMoveDuration, LoopAnimUpdate);
    }
  }

  if ((boilerState != currentboilerState) || forceUpdate == 1) {

    if (animations.IsAnimationActive(3)) {
      exit;
    }
    else {
      FadeBoiler(0.2f); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }

  }

  if ((veraState != currentveraState) || forceUpdate == 1) {

    if (animations.IsAnimationActive(2)) {
      exit;
    }
    else {
      FadeVera(0.2f); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }

  }

  if ((cubeState != currentcubeState) || forceUpdate == 1) {

    if (animations.IsAnimationActive(1)) {
      exit;
    }
    else {
      FadeCube(0.2f); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }

  }


  if (heatState == 1) {
    
    if (animations.IsAnimationActive(0) && currentheatState == 1) {
      exit;
    }
    else if (heatCycle < heatTime) {
      currentheatState = 1;
      FadeInFadeOutRinseRepeat(0.1f, 360); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }
  }

  if (heatState == 0) {
    if (animations.IsAnimationActive(0) && currentheatState == 0) {
      exit;
    }
    else if (heatCycle < heatTime) {
      currentheatState = 0;
      FadeInFadeOutRinseRepeat(0.1f, 200); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }
  }

  if (heatState == 2 && effectState == 1) {
    //Serial.println("Starting animation blue beat");
    if (animations.IsAnimationActive(0)) {
      currentheatState = 2;
      FadeInFadeOutRinseRepeat(0.1f, 200); // 0.0 = black, 0.25 is normal, 0.5 is bright
    }
  }

  if (lightArg == 1) {
    animations.Pause();
    RgbColor white(128);
    RgbColor black(0);
    for (int i = 0; i < 3; i++) {
      for (int x = 0; x < 4; x++) {
        strip.SetPixelColor(3, white);
        delay(100);
        strip.Show();
        strip.SetPixelColor(3, black);
        delay(100);
        strip.Show();
      }
    }
    animations.Resume();
    lightArg = 0;
    SetLights();
  }

  if (lightArg == 2) {
    animations.Pause();
    RgbColor white(128);
    RgbColor black(0);
    for (int i = 0; i < 3; i++) {
      for (int x = 0; x < 4; x++) {
        strip.SetPixelColor(9, white);
        delay(100);
        strip.Show();
        strip.SetPixelColor(9, black);
        delay(100);
        strip.Show();
      }
    }
    animations.Resume();
    lightArg = 0;
    SetLights();
  }
}

void setup()
{
  pinMode(BOILER_BUTTON, INPUT_PULLUP);
  pinMode(CHECK_BUTTON, INPUT_PULLUP);
  pinMode(OVER_BUTTON, INPUT_PULLUP);
  pinMode(REBOOT_BUTTON, INPUT_PULLUP);
  pinMode(SHUTDOWN_BUTTON, INPUT_PULLUP);
  
  pinMode(RELAY_OUT, OUTPUT);
  digitalWrite(RELAY_OUT, HIGH);

  Serial.begin(115200);
  strip.Begin();
  strip.Show();
}

void loop()
{

  if (Serial.available() > 0) {
    String chase = Serial.readStringUntil(',');
    Serial.read();
    String heat = Serial.readStringUntil(',');
    Serial.read();
    String heattime = Serial.readStringUntil(',');
    Serial.read();
    String boiler = Serial.readStringUntil(',');
    Serial.read();
    String cube = Serial.readStringUntil(',');
    Serial.read();
    String vera = Serial.readStringUntil(',');
    Serial.read();
    String over = Serial.readStringUntil(',');
    Serial.read();
    String light = Serial.readStringUntil(',');

    chaseState = chase.toInt();
    if (chaseState == 1) {
      chaseCycle = 0;
    }
    heatState = heat.toInt();
    heatTime = (heattime.toInt() / 8);
    heatCycle = 0;
    boilerState = boiler.toInt();
    cubeState = cube.toInt();
    veraState = vera.toInt();
    overrideState = over.toInt();
    lightArg = light.toInt();

    if (heatState == 1) {
      digitalWrite(RELAY_OUT, LOW);
    }
    else {
      digitalWrite(RELAY_OUT, HIGH);
    }


  }
  //SetLights();

  int boilerSW = digitalRead(BOILER_BUTTON);
  int checkSW = digitalRead(CHECK_BUTTON);
  int overSW = digitalRead(OVER_BUTTON);
  int rebootSW = digitalRead(REBOOT_BUTTON);
  int shutdownSW = digitalRead(SHUTDOWN_BUTTON);

  if (boilerSW != boilerBtnState) {
    if (boilerSW == 0) {
      Serial.println("boilerSW_ON");
    }
    else {
      Serial.println("boilerSW_OFF");
    }
    delay(50);
  }
  boilerBtnState = boilerSW;

  if (checkSW != checkBtnState) {
    if (checkSW == 0) {
      Serial.println("checkSW_ON");
    }
    else {
      Serial.println("checkSW_OFF");
    }
    delay(50);
  }
  checkBtnState = checkSW;

  if (overSW != overBtnState) {
    if (overSW == 0) {
      Serial.println("overSW_ON");
    }
    else {
      Serial.println("overSW_OFF");
    }
    delay(50);
  }
  overBtnState = overSW;

  if (rebootSW != rebootBtnState) {
    if (rebootSW == 0) {
      Serial.println("rebootSW_ON");
    }
    else {
      Serial.println("rebootSW_OFF");
    }
    delay(50);
  }
  rebootBtnState = rebootSW;

  if (shutdownSW != shutdownBtnState) {
    if (shutdownSW == 0) {
      Serial.println("shutdownSW_ON");
    }
    else {
      Serial.println("shutdownSW_OFF");
    }
    delay(50);
  }
  shutdownBtnState = shutdownSW;

  SetLights();

  if (animations.IsAnimating())
  {
    // the normal loop just needs these two to run the active animations
    //Serial.println("update anim");
    animations.UpdateAnimations();
    strip.Show();
  }
}



