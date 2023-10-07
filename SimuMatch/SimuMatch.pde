

void setup(){
  size(900, 600);
  background(color(#ED4B00));
  frameRate(30);
  smooth();
}

void draw(){
  drawTerrain();
}

void drawTerrain(){
  background(color(#ED4B00));
  
  //Carrés de gauche
  fill(0,0,150);
  rect(0,0,135,135);
  fill(200,200,0);
  rect(0,232.5,135,135);
  fill(0,0,150);
  rect(0,465,135,135);
  
  //Carrés de droite
  fill(200,200,0);
  rect(765,0,135,135);
  fill(0,0,150);
  rect(765,232.5,135,135);
  fill(200,200,0);
  rect(765,465,135,135);
  
  //Case des coccinelles
  fill(0,200,0);
  rect(250,0,200,50);
  rect(450,0,200,50);
}
