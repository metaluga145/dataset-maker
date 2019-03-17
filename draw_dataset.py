"""
A paint-style 2D toy dataset builder.
The user clicks on the canvas to create groups of normally distributed points in one of the
3 available colors. The canvas can be cleared, or the last point undone.
Dataset is scaled to zero mean and unit variance before saving.
The dataset created can be saved to a .csv file. 
"""

import tkinter as tk
from tkinter import filedialog as tkFileDialog
from numpy.random import normal
import pandas as pd
from sklearn import preprocessing

class Dataset:
    """
    A class managing the data created by the user and displaying it on a Tkinter canvas.
    """

    def __init__(self, drawingArea, sigmaScatter, nbrPointsScatter):
        """
        Initialize with an empty dataset.
        Args: 
          drawingArea (tk.Canvas): canvas for displaying the dataset
          sigmaScatter (tk.DoubleVar): spread of a group of points created by a click
          nbrPointsScatter (tk.DoubleVar): number of points per click group
        """
        # myData is a list of coordinates and color for each point in the dataset
        self.myData = []
        # tkinter IDs for each data point
        self.myPointsID = []
        # marker size for the point
        self.sizePoint = 2
        # Current class (color) attributed to next points being drawn ("blue", "green", "red")
        self.classPoint = "blue"
        self.drawingArea = drawingArea
        self.sigmaScatter = sigmaScatter
        self.nbrPointsScatter = nbrPointsScatter
        self.last_drawn_x = None
        self.last_drawn_y = None
        self.threshold = 5

    def setClass(self, color):
        """
        Change point color
        Args: 
          color (String): color for the next points that will be created
        """
        self.classPoint = color

    def pressButton(self, event):
        self.last_drawn_x = event.x
        self.last_drawn_y = event.y
        
        if self.classPoint == "erase":
            self._delete_points(event)
        else:
            self.makeScatter(event)
    
    def moveButton(self, event):
        if self.last_drawn_x is None:
            return

        move_distance = (self.last_drawn_x - event.x) ** 2  + (self.last_drawn_y - event.y) ** 2
        if move_distance >= self.threshold ** 2:
            self.pressButton(event)

    def releaseButton(self, event):
        self.moveButton(event)

        self.last_drawn_x = None
        self.last_drawn_y = None

    def _draw_point(self, x, y, pointClass):
        newpoint = self.drawingArea.create_oval(x - self.sizePoint, y - self.sizePoint,
                                                x + self.sizePoint, y + self.sizePoint,
                                                fill=pointClass)
        self.myPointsID.append(newpoint)
        self.myData.append((x, y, pointClass))

    def _delete_points(self, event):
        threshold = self.sigmaScatter.get()
        threshold = threshold * threshold

        lst_to_del = []
        for i, coord in enumerate(self.myData):
            x, y, color = coord
            if (x - event.x) ** 2 + (y - event.y) ** 2 <= threshold:
                lst_to_del.append(i)
        print("deleting: ", lst_to_del)
        for i in lst_to_del:
            self.drawingArea.delete(self.myPointsID[i])

        self.myData = [val for i,val in enumerate(self.myData) if i not in lst_to_del]
        self.myPointsID = [val for i,val in enumerate(self.myPointsID) if i not in lst_to_del]


    def makeScatter(self, event):
        """
        Draw points sampled from a gaussian distribution around the click point
        Args:
          event (tk.Event): tk user click event
        """
        # clamp values to a reasonable interval
        ss = max(min(self.sigmaScatter.get(), 50), 0)
        ps = max(min(self.nbrPointsScatter.get(), 1000), 0)
        listX = normal(loc=event.x, scale=ss, size=int(ps))
        listY = normal(loc=event.y, scale=ss, size=int(ps))
        for (x,y) in zip(listX, listY):
            self.myData.append([x, y, self.classPoint])
            newpoint = event.widget.create_oval(x-self.sizePoint, y-self.sizePoint, 
                                                x+self.sizePoint, y+self.sizePoint,
                                                fill=self.classPoint)
            self.myPointsID.append(newpoint)

    def saveData(self):
        """
        Save the x,y,class properties of each drawn points to a csv file.
        Dataset is scaled to zero mean and unit variance before saving.
        """
        saveTo = tkFileDialog.asksaveasfile(mode='w', defaultextension="")
        if saveTo is None:
            return None
        df = pd.DataFrame(self.myData, columns = ["x","y","color"])
        #scale to zero mean and unit variance
        #df[['x','y']] = df[['x','y']].apply(lambda x: preprocessing.scale(x))
        #df['x'] = (df['x'] - df['x'].min()) / (df['x'].max() - df['x'].min())
        #df['y'] = (df['y'] - df['y'].min()) / (df['y'].max() - df['y'].min())
        df['color'] = df['color'].replace({"red": 0, "green": 1, "blue": 2})
        df.to_csv(saveTo.name, index=False)
        saveTo.close()

    def loadData(self):
        """
        Load points from the csv file
        """
        loadFrom = tkFileDialog.askopenfilename()
        df = pd.read_csv(loadFrom)
        df['color'] = df['color'].replace({0: "red", 1: "green", 2: "blue"})
        
        df.apply(lambda row: self._draw_point(row['x'], row['y'], row['color']), axis=1)

    def clearCanvas(self):
        """
        Remove all points on canvas.
        """
        for pointID in self.myPointsID:
            self.drawingArea.delete(pointID)
        self.myPointsID = []
        self.myData = []

    def undo(self):
        """
        Remove the last drawn point. Raises exception if no points are defined.
        """
        self.myData.pop()
        self.drawingArea.delete(self.myPointsID.pop())


if __name__ == "__main__":
    
    # build TK window
    root = tk.Tk()
    root.wm_title("Draw Dataset")
    # for the points
    drawingArea = tk.Canvas(root, width=600, height=600)
    # for the parameters
    frameVars = tk.Frame(root, bd=2)

    # drawing parameters default values
    sigmaScatter = tk.DoubleVar(value='10')
    nbrPointsScatter = tk.DoubleVar(value='5')

    # create display for parameter edition
    tk.Label(frameVars, text='stdDEV').pack(side=tk.LEFT)
    esigma = tk.Entry(frameVars,
                      textvariable = sigmaScatter).pack(side=tk.LEFT,padx=3)
    tk.Label(frameVars, text='nbrPoints').pack(side=tk.LEFT)
    escatter = tk.Entry(frameVars,
                        textvariable = nbrPointsScatter).pack(side=tk.LEFT,padx=3)

    # create windows
    drawingArea.create_window(1, 1, anchor=tk.NW, window=frameVars)
    frameVars.pack(anchor=tk.NW)
    drawingArea.pack()

    data = Dataset(drawingArea, sigmaScatter, nbrPointsScatter)

    # bind mouse click to point drawing
    drawingArea.bind("<Button>", data.pressButton)
    drawingArea.bind("<Motion>", data.moveButton)
    drawingArea.bind("<ButtonRelease>", data.releaseButton)

    # button positioning parameters
    width = 5
    sep = 60
    margin = 5
    
    # point color buttons
    bcolorBlue = tk.Button(root, text="blue", command=lambda: data.setClass("blue"), width=width)
    drawingArea.create_window(margin, 10, anchor=tk.NW, window=bcolorBlue)

    bcolorRed = tk.Button(root, text="red", command=lambda: data.setClass("red"), width=width)
    drawingArea.create_window(margin+sep, 10, anchor=tk.NW, window=bcolorRed)

    bcolorGreen = tk.Button(root, text="green", command=lambda: data.setClass("green"), width=width)
    drawingArea.create_window(margin+2*sep, 10, anchor=tk.NW, window=bcolorGreen)

    # dataset actions buttons
    bsave = tk.Button(root, text="save", command=data.saveData, width=width)
    drawingArea.create_window(margin+3*sep, 10, anchor=tk.NW, window=bsave)

    bload = tk.Button(root, text="load", command=data.loadData, width=width)  
    drawingArea.create_window(margin+4*sep, 10, anchor=tk.NW, window=bload)

    bclear = tk.Button(root, text="clear", command=data.clearCanvas, width=width)
    drawingArea.create_window(margin+5*sep, 10, anchor=tk.NW, window=bclear)

    bundo = tk.Button(root, text="undo", command=data.undo, width=width)
    drawingArea.create_window(margin+6*sep, 10, anchor=tk.NW, window=bundo)

    berase = tk.Button(root, text="erase", command=lambda: data.setClass("erase"), width=width)
    drawingArea.create_window(margin+7*sep, 10, anchor=tk.NW, window=berase)

    tk.mainloop()
