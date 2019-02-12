# a simple Clamity-like environment
# discrete state and action spaces
# the agent receives 0 reward until it decides to stop
    # then it receives however much reward is marked on the grid at that spot
    # stopping ends the episode

import numpy as np

trail_decay = 0.2

class ActionSpace():
    def __init__(self, actions_tuple):
        self.actions = actions_tuple
        self.np_random = np.random.RandomState()
    
    def sample(self):
        action = self.np_random.randint(0, len(self.actions))
        return action


class ClamEnv():
    def __init__(self, trail=False):
        # grid setup
        self.height = 15
        self.width = 15
        self.start = (self.height//2,self.width//2)
        self.grid = np.zeros((self.height, self.width))
        r_row = (self.height-3)//4  # rows from top and bottom where the rewards are
        r_col = (self.width-3)//4   # columns from left and right where the rewards are
        self.grid[r_row,r_col] = 3
        self.grid[r_row,self.width-r_col-1] = 4
        self.grid[self.height-r_row-1,r_col] = 5
        self.grid[self.height-r_row-1,self.width-r_col-1] = 6
        self.grid[self.start[0], self.start[1]] = 2

        # trail of negative reward the agent leaves in its wake
        self.trail = trail
        self.trail_grid = np.zeros((self.height, self.width))

        # observation grid
        self.window_size = 3    # should be an odd number
        self.obs_height = self.height+self.window_size-1
        self.obs_width = self.width+self.window_size-1
        self.wall_depth = (self.window_size - 1)//2
        self.obs_grid = -2*np.ones((self.obs_height, self.obs_width))
        self.update_obs_grid()

        self.action_space = ActionSpace(("left","right","up","down","stop"))
        self.reset()


    # updates the grid from which agent observations are taken
    def update_obs_grid(self):
        self.obs_grid[self.wall_depth:self.obs_height-self.wall_depth,self.wall_depth:self.obs_width-self.wall_depth] \
                = self.grid + self.trail_grid


    # resets to start position
    def reset(self):
        self.state = list(self.start)
        return self.state


    # action is an index into possible action tuple
    # returns (reward, done)
    def step(self, action):
        row, col = self.state

        # transition to next state
        if self.action_space.actions[action] == "stop":
            reward = self.grid[row, col]
            done = True
            self.reset()
        else:
            if self.action_space.actions[action] == "left":
                self.state = [row, max(0, col-1)]
            elif self.action_space.actions[action] == "right":
                self.state = [row, min(self.width-1, col+1)]
            elif self.action_space.actions[action] == "up":
                self.state = [max(0, row-1), col]
            else: # if action == "down":
                self.state = [min(self.height-1, row+1), col]
            reward = 0
            done = False

        # handle if we're using trails
        if self.trail:
            if done:
                reward += self.trail_grid[row,col]  # penalize reward if an agent has been to this state recently
            self.trail_grid = np.minimum(0, self.trail_grid + trail_decay)  # decay trail
            self.trail_grid[row, col] = -1  # extend end of trail to last state visited
            self.update_obs_grid()  # put trails on observation space

        return self.obs_fn(self.state), reward, done, {} # openai gym convention


    # observation function
    # returns a window_size x window_size view of the environment centered at the agent's position
    def obs_fn(self, state):
        row = state[0]+self.wall_depth    # row and column in observation grid
        col = state[1]+self.wall_depth
        window = self.obs_grid[row-self.wall_depth:row+self.wall_depth+1,col-self.wall_depth:col+self.wall_depth+1]
        window =  window.ravel()   # flattened for input to dense layers
        window = np.array([window]) # extra dimension of size 1 added because dense layers expect a batch dimension
        return window
             
    # convenience function to return the current observation
    def obs(self):
        return self.obs_fn(self.state)

